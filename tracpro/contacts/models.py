from __future__ import absolute_import, unicode_literals

import datetime
import traceback
from decimal import Decimal, InvalidOperation
import logging
from uuid import uuid4
from enum import Enum

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import force_text
from django.utils.translation import ugettext_lazy as _

from dash.utils import datetime_to_ms

from temba_client.v2.types import Contact as TembaContact, ObjectRef

from tracpro.client import get_client
from tracpro.contacts.fields import URN_SCHEME_LABELS
from tracpro.groups.models import Region, Group
from tracpro.orgs_ext.constants import TaskType
from tracpro.utils import get_uuids

from .tasks import push_contact_change
from .utils import sync_pull_contacts


logger = logging.getLogger(__name__)


class NoContactInRapidProWarning(Exception):
    """
    Raised when we try to get a remote contact and it doesn't exist.
    """
    pass


class NoMatchingCohortsWarning(Exception):
    """
    Have Contact.kwargs_from_temba be a little more specific about this case by
    raising this exception.
    """
    pass


class NoUsableURNWarning(Exception):
    pass


class ChangeType(Enum):
    created = 1
    updated = 2
    deleted = 3


class ContactQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def by_org(self, org):
        return self.filter(org=org)

    def by_regions(self, regions):
        return self.filter(region__in=regions)


class ContactManager(models.Manager.from_queryset(ContactQuerySet)):

    def create(self, *args, **kwargs):
        contact_groups = kwargs.pop('groups', [])
        new_contact = super(ContactManager, self).create(*args, **kwargs)
        new_contact.groups = contact_groups
        return new_contact

    def sync(self, org):
        try:
            region_uuids = set(get_uuids(Region.get_all(org)))
            group_uuids = set(get_uuids(Group.get_all(org)))

            created, updated, deleted, failed, errors = sync_pull_contacts(
                org=org,
                region_uuids=region_uuids,
                group_uuids=group_uuids
            )

            org.set_task_result(TaskType.sync_contacts, {
                'time': datetime_to_ms(timezone.now()),
                'counts': {
                    'created': len(created),
                    'updated': len(updated),
                    'deleted': len(deleted),
                    'failed': len(failed),
                },
            })
        except:
            logger.exception("EXCEPTION in ContactManager.sync")
            return [traceback.format_exc()]
        return errors


@python_2_unicode_compatible
class Contact(models.Model):
    """Corresponds to a RapidPro contact."""

    uuid = models.CharField(max_length=36)
    org = models.ForeignKey(
        'orgs.Org', verbose_name=_("Organization"), related_name="contacts")
    name = models.CharField(
        verbose_name=_("Full name"), max_length=128, blank=True,
        help_text=_("The name of this contact"))
    urn = models.CharField(
        verbose_name=_("Phone/Twitter"),
        max_length=255,
        help_text=_("Phone number or Twitter handle of this contact."))
    region = models.ForeignKey(
        'groups.Region', verbose_name=_("Panel"), related_name='contacts',
        help_text=_("Panel of this contact."))
    groups = models.ManyToManyField(
        'groups.Group', verbose_name=_("Cohorts"),
        related_name='contacts',
        help_text=_("All cohorts to which this contact belongs."))
    language = models.CharField(
        max_length=3, verbose_name=_("Language"), null=True, blank=True,
        help_text=_("Language for this contact"))

    # Metadata.
    is_active = models.BooleanField(
        default=True, help_text=_("Whether this contact is active"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="contact_creations",
        help_text="The user which originally created this item")
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text="When this item was originally created")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="contact_modifications",
        help_text="The user which last modified this item")
    modified_on = models.DateTimeField(
        auto_now=True,
        help_text="When this item was last modified")
    temba_modified_on = models.DateTimeField(
        null=True,
        help_text="When this item was last modified in Temba",
        editable=False)

    objects = ContactManager()

    class Meta:
        unique_together = [
            ('uuid', 'org'),
        ]

    def __init__(self, *args, **kwargs):
        self._data_field_values = kwargs.pop('_data_field_values', None)
        super(Contact, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.name or self.get_urn()[1]

    def as_temba(self):
        """Return a Temba object representing this Contact."""
        fields = {f.field.key: f.get_value() for f in self.contactfield_set.all()}

        # Include all the groups associated with the contact.
        # In Temba v2, we get back ObjectRefs for these, so imitate that here.
        groups = [ObjectRef.create(uuid=group.uuid, name=group.name)
                  for group in self.groups.all()]

        if self.region and self.region.uuid not in get_uuids(groups):
            groups.append(ObjectRef.create(uuid=self.region.uuid, name=self.region.name))

        return TembaContact.create(
            name=self.name,
            urns=[self.urn],
            fields=fields,
            groups=groups,
            language=self.language,
            uuid=self.uuid,
            blocked=not self.is_active,
            modified_on=self.modified_on
        )

    def delete(self):
        """Deactivate the local copy & delete from RapidPro."""
        self.is_active = False
        self.save()
        self.push(ChangeType.deleted)

    @classmethod
    def get_or_fetch(cls, org, uuid):
        """Gets a contact by UUID.

        If we don't find them locally, we try to fetch them from RapidPro.

        Can raise NoContactInRapidProWarning or NoMatchingCohortsWarning.
        """
        contacts = cls.objects.filter(org=org).select_related('region')
        try:
            return contacts.get(uuid=uuid)
        except cls.DoesNotExist:
            # If this contact does not exist locally, we need to call the RapidPro API to get it
            temba_contacts = get_client(org).get_contacts(uuid=uuid)
            if not temba_contacts:
                # Probably shouldn't happen - but does
                raise NoContactInRapidProWarning("No contact in RapidPro with uuid=%s" % uuid)
            temba_contact = temba_contacts[0]
            # NB: Contact.kwargs_from_temba can raise NoMatchingCohortsWarning
            return cls.objects.create(**cls.kwargs_from_temba(org, temba_contact))

    def get_responses(self, include_empty=True):
        from tracpro.polls.models import Response
        qs = self.responses.filter(pollrun__poll__is_active=True, is_active=True)
        qs = qs.select_related('pollrun')
        if not include_empty:
            qs = qs.exclude(status=Response.STATUS_EMPTY)
        return qs

    def get_urn(self):
        return tuple(self.urn.split(':', 1))

    @classmethod
    def kwargs_from_temba(cls, org, temba_contact):
        """Get data to create a Contact instance from a Temba object."""

        def _get_first(model_class, temba_objects):
            """Return first obj from this org that matches one of the given uuids, or None."""

            queryset = model_class.get_all(org)
            temba_uuids = get_uuids(temba_objects)

            # '.first()' doesn't really mean first
            # there should only be one region here
            return queryset.filter(uuid__in=temba_uuids).order_by('name').first()

        # Use the first Temba group that matches one of the org's Regions.
        region = _get_first(Region, temba_contact.groups)

        if not region:
            raise NoMatchingCohortsWarning(
                "Unable to save contact {c.name} ({c.uuid}) because none of "
                "their RapidPro Groups match an active Panel for this org.".format(
                    c=temba_contact,
                ))

        # Make a list of groups that the Contact belongs to.
        # Use all the Temba groups that match a group (cohort) in Tracpro.
        # We INCLUDE groups that the org is not currently tracking, because otherwise
        # we might end up pushing the subset of groups belonged to back to Rapidpro,
        # resulting in losing the data about the other groups the contact belonged to.
        # Including non-tracked groups in the contact's cohorts should be harmless -
        # we only ever check to see if a cohort we're tracking is in the contact's
        # cohorts, and will never even notice the other groups.
        groups = Group.objects.filter(uuid__in=get_uuids(temba_contact.groups))

        # Use the first URN we know about the scheme of
        urn = None
        for u in temba_contact.urns:
            scheme, value = u.split(':', 1)
            if scheme in URN_SCHEME_LABELS:
                urn = u
                break  # it's a urn we can use
        if urn is None:
            raise NoUsableURNWarning(
                "Unable to save contact {c.name} ({c.uuid}) because none of "
                "their URNs ({c.urns}) are for schemes that tracpro supports ({schemes})".format(
                    c=temba_contact,
                    schemes=URN_SCHEME_LABELS.keys(),
                )
            )

        kwargs = {
            'org': org,
            'name': temba_contact.name or "",
            'urn': urn,
            'region': region,
            'groups': groups,
            'language': temba_contact.language,
            'uuid': temba_contact.uuid,
            'temba_modified_on': temba_contact.modified_on,
            '_data_field_values': temba_contact.fields,  # managed by post-save signal
        }
        if cls.objects.filter(org=org, uuid=temba_contact.uuid).exists():
            # Note that 'groups' is only a valid kwarg if the contact already exists
            kwargs['groups'] = list(Group.objects.filter(uuid__in=get_uuids(temba_contact.groups)))
        return kwargs

    def push(self, change_type):
        push_contact_change.delay(self.pk, change_type)

    def save(self, *args, **kwargs):
        if self.org.pk != self.region.org_id:
            raise ValidationError("Panel does not belong to Org.")

        # write a validation error for 'groups' below?
        # if self.group and self.org.pk != self.group.org_id:
        #     raise ValidationError("Cohort does not belong to Org.")

        # RapidPro might return blank or null values.
        self.name = self.name or ""

        if not self.uuid:
            # There will be no UUID if we are creating this Contact
            # (rather than importing from RapidPro).
            # Create a temporary but unique UUID.
            # NOTE: This UUID will be updated when the new Contact is pushed
            # to RapidPro!
            self.uuid = str(uuid4())
            push_created = True
        else:
            push_created = False

        contact = super(Contact, self).save(*args, **kwargs)

        if push_created:
            self.push(ChangeType.created)

        return contact

    def fields(self):
        return {f.field.key: f.value for f in self.contactfield_set.all()}


class DataFieldQuerySet(models.QuerySet):

    def visible(self):
        return self.filter(show_on_tracpro=True)

    def by_org(self, org):
        return self.filter(org=org)


class DataFieldManager(models.Manager.from_queryset(DataFieldQuerySet)):

    def from_temba(self, org, temba_field):
        field, _ = DataField.objects.get_or_create(org=org, key=temba_field.key)
        field.label = temba_field.label
        field.value_type = DataField.MAP_V2_TYPE_VALUE_TO_DB_VALUE[temba_field.value_type]
        field.save()
        return field

    def sync(self, org):
        """Update the org's DataFields from RapidPro."""
        # Retrieve current DataFields known to RapidPro.
        temba_fields = {t.key: t for t in get_client(org).get_fields()}

        # Remove DataFields (and corresponding values per contact) that are no
        # longer on RapidPro.
        DataField.objects.by_org(org).exclude(key__in=temba_fields.keys()).delete()

        # Create new or update existing DataFields to match RapidPro data.
        for temba_field in temba_fields.values():
            DataField.objects.from_temba(org, temba_field)

    def set_active_for_org(self, org, keys):
        fields = DataField.objects.by_org(org)
        fields.filter(key__in=keys).update(show_on_tracpro=True)
        fields.exclude(key__in=keys).update(show_on_tracpro=False)


class DataField(models.Model):
    """Custom contact data fields defined on RapidPro.

    https://app.rapidpro.io/api/v1/fields
    """
    TYPE_TEXT = "T"
    TYPE_NUMERIC = "N"
    TYPE_DATETIME = "D"
    TYPE_STATE = "S"
    TYPE_DISTRICT = "I"
    TYPE_DECIMAL = 'N'  # New in v2 API
    TYPE_WARD = 'W'  # New in v2 API
    TYPE_CHOICES = (
        (TYPE_TEXT, _("Text")),
        (TYPE_NUMERIC, _("Numeric")),
        (TYPE_DATETIME, _("Datetime")),
        (TYPE_STATE, _("State")),
        (TYPE_DISTRICT, _("District")),
        (TYPE_DECIMAL, _("Numeric")),
        (TYPE_WARD, _("Ward")),
    )

    # This is copied from the rapidpro source
    # The v1 API sent us the single-characters above.
    # The v2 API sends us the 3rd element from each tuple here.
    API_V2_TYPE_CONFIG = ((TYPE_TEXT, _("Text"), 'text'),
                          (TYPE_DECIMAL, _("Numeric"), 'numeric'),
                          (TYPE_DATETIME, _("Date & Time"), 'datetime'),
                          (TYPE_STATE, _("State"), 'state'),
                          (TYPE_DISTRICT, _("District"), 'district'),
                          (TYPE_WARD, _("Ward"), 'ward'))

    # v2 value: v1 value
    MAP_V2_TYPE_VALUE_TO_DB_VALUE = {tup[2]: tup[0] for tup in API_V2_TYPE_CONFIG}

    org = models.ForeignKey(
        "orgs.Org", verbose_name=_("org"))
    label = models.CharField(
        max_length=255, blank=True, verbose_name=_("label"))
    key = models.CharField(
        max_length=255, verbose_name=_("key"))
    value_type = models.CharField(
        max_length=1, choices=TYPE_CHOICES, verbose_name=_("value type"))
    show_on_tracpro = models.BooleanField(
        default=False, verbose_name=_("show on TracPro"))

    objects = DataFieldManager()

    class Meta:
        ordering = ('label', 'key')
        unique_together = [('org', 'key')]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return (self.label or self.key).title()

    def get_form_field(self, **kwargs):
        if self.value_type == DataField.TYPE_DATETIME:
            field_type = forms.DateTimeField
        elif self.value_type == DataField.TYPE_NUMERIC:
            field_type = forms.DecimalField
        else:
            field_type = forms.CharField
        return field_type(label=self.display_name, required=False, **kwargs)


class ContactFieldQuerySet(models.QuerySet):

    def visible(self):
        return self.filter(field__show_on_tracpro=True)


class ContactField(models.Model):
    """Many-to-many relationship to represent a Contact's value for a DataField."""
    contact = models.ForeignKey('contacts.Contact')
    field = models.ForeignKey('contacts.DataField')
    value = models.CharField(max_length=255, null=True)

    objects = ContactFieldQuerySet.as_manager()

    def __str__(self):
        return "{} {}: {}".format(self.contact, self.field, self.get_value())

    def get_value(self):
        """Retrieve the value of this instance according to the DataField type."""
        if self.value is None:
            return None
        elif self.field.value_type == DataField.TYPE_DATETIME:
            return parse_datetime(self.value)
        elif self.field.value_type == DataField.TYPE_NUMERIC:
            try:
                return Decimal(self.value)
            except InvalidOperation:
                logger.warning(
                    "Unable to parse {} value for {} as decimal: {}".format(
                        self.field, self.contact, self.value))
                return None
        else:
            return self.value

    def set_value(self, value):
        """Serialize the value on this instance according to its type."""
        if value is None:
            self.value = None
        elif isinstance(value, datetime.datetime):
            self.value = unicode(value.isoformat())
        else:
            self.value = force_text(value)
