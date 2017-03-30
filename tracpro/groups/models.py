from __future__ import absolute_import, unicode_literals

import json
from operator import attrgetter

from dateutil.relativedelta import relativedelta

from mptt import models as mptt

from django.conf import settings
from django.db import models, transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.client import get_client
from tracpro.contacts.tasks import SyncOrgContacts


@python_2_unicode_compatible
class AbstractGroup(models.Model):
    """Corresponds to a RapidPro contact group."""

    uuid = models.CharField(max_length=36)
    org = models.ForeignKey(
        'orgs.Org', verbose_name=_("Organization"), related_name="%(class)ss")
    name = models.CharField(
        verbose_name=_("Name"), max_length=128, blank=True,
        help_text=_("The name of this panel"))
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this item is active"))

    class Meta:
        abstract = True
        unique_together = [
            ('org', 'uuid'),
        ]

    def __str__(self):
        return self.name

    def deactivate(self):
        self.is_active = False
        self.save()

    @classmethod
    def sync_with_temba(cls, org, uuids):
        """Sync org groups with the selected UUIDs."""
        # De-activate any groups that are not specified.
        other_groups = cls.objects.filter(org=org, is_active=True)
        other_groups = other_groups.exclude(uuid__in=uuids)
        for group in other_groups:
            group.deactivate()

        # Fetch group details at once.
        temba_groups = get_client(org).get_groups()
        temba_groups = {g.uuid: g.name for g in temba_groups}

        for uuid in uuids:
            if uuid in temba_groups:
                # Create a new item or update an existing one.
                obj, _ = cls.objects.get_or_create(org=org, uuid=uuid)
                obj.is_active = True
                obj.name = temba_groups.get(uuid)
                obj.save()
            else:
                # The group was removed remotely and should be removed locally.
                obj = cls.objects.filter(org=org, uuid=uuid).first()
                if obj:
                    obj.deactivate()

        SyncOrgContacts().delay(org.pk)

    @classmethod
    def get_all(cls, org):
        return cls.objects.filter(org=org, is_active=True)

    @classmethod
    def get_response_counts(cls, org, include_empty=False):
        """Return response counts from the last 30 days."""
        from tracpro.polls.models import Response
        qs = Response.objects.filter(pollrun__poll__org=org, is_active=True)

        if not include_empty:
            qs = qs.exclude(status=Response.STATUS_EMPTY)

        window_max = timezone.now()
        window_min = window_max - relativedelta(days=30)
        qs = qs.filter(updated_on__gte=window_min, updated_on__lt=window_max)

        field = 'contact__%s' % cls.__name__.lower()

        qs = qs.filter(**{'%s__is_active' % field: True})
        counts = qs.values(field).annotate(count=Count(field))
        return {count[field]: count['count'] for count in counts}

    @classmethod
    def get_most_active(cls, org):
        count_by_id = cls.get_response_counts(org, include_empty=False)
        groups = []
        for group in cls.get_all(org):
            count = count_by_id.get(group.pk, 0)
            if count:
                group.response_count = count
                groups.append(group)
        return sorted(groups, key=lambda g: g.response_count, reverse=True)

    def get_contacts(self):
        return self.contacts.filter(is_active=True)


class Region(mptt.MPTTModel, AbstractGroup):
    """A geographical region modelled as a group."""
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("Users"), related_name='regions',
        help_text=_("Users who can access this panel"))
    parent = mptt.TreeForeignKey(
        'self', null=True, blank=True, related_name="children", db_index=True)
    boundary = models.ForeignKey(
        'groups.Boundary',
        null=True,
        verbose_name=_('boundary'),
        related_name='regions',
        on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'panel'

    class MPTTMeta:
        order_insertion_by = ['name']

    @transaction.atomic
    def deactivate(self):
        # Make this region's parent the parent of all of its children.
        with Region.objects.disable_mptt_updates():
            for child in self.get_children():
                child.parent = self.parent
                child.save()
        Region.objects.rebuild()

        # Move this node out of the tree.
        # If this region is re-activated, it will appear at the top level.
        self.parent = None

        super(Region, self).deactivate()

    def get_users(self):
        return self.users.filter(is_active=True).select_related('profile')

    @classmethod
    def sync_with_temba(cls, org, uuids):
        """Rebuild the tree hierarchy after new nodes are added."""
        super(Region, cls).sync_with_temba(org, uuids)
        Region.objects.rebuild()


class Group(AbstractGroup):
    """A data reporting group."""
    class Meta:
        verbose_name = 'cohort'


# === Boundaries === #


class BoundaryQuerySet(models.QuerySet):

    def by_org(self, org):
        return self.filter(org=org)


class BoundaryManager(models.Manager.from_queryset(BoundaryQuerySet)):

    def from_temba(self, org, temba_boundary):
        """Get the existing or create a new corresponding Boundary instance.

        Assumes that the boundary's parent, if any, has already been created.
        """
        boundary, _ = self.get_or_create(org=org, rapidpro_uuid=temba_boundary.osm_id)
        boundary.name = temba_boundary.name
        boundary.level = temba_boundary.level
        boundary.geometry = json.dumps(temba_boundary.geometry.serialize())
        boundary.parent = self.filter(org=org, rapidpro_uuid=temba_boundary.parent).first()
        boundary.save()
        return boundary

    def sync(self, org):
        """Update org Boundaries from RapidPro and delete ones that were removed."""
        # Retrieve current Boundaries known to RapidPro.
        temba_boundaries = list(get_client(org).get_boundaries())

        # Remove Boundaries that are no longer on RapidPro.
        uuids = [b.osm_id for b in temba_boundaries]
        Boundary.objects.by_org(org).exclude(rapidpro_uuid__in=uuids).delete()

        # Order boundaries from the highest level (country) to the lowest
        # (district). This ensures that each boundary's parent (if any)
        # has been  created before it is updated.
        temba_boundaries.sort(key=attrgetter('level'))

        # Create new or update existing Polls to match RapidPro data.
        for temba_boundary in temba_boundaries:
            Boundary.objects.from_temba(org, temba_boundary)


class Boundary(models.Model):
    """Corresponds with a RapidPro AdminBoundary."""

    LEVEL_COUNTRY = 0
    LEVEL_STATE = 1
    LEVEL_DISTRICT = 2
    LEVEL_CHOICES = (
        (LEVEL_COUNTRY, _("Country")),
        (LEVEL_STATE, _("State")),
        (LEVEL_DISTRICT, _("District")),
    )

    org = models.ForeignKey(
        'orgs.Org',
        verbose_name=_("org"))

    rapidpro_uuid = models.CharField(
        max_length=15,
        verbose_name=_("RapidPro UUID"),
        help_text=_("Not a standard UUID; rather, it is a variation of the OSM ID."))
    name = models.CharField(
        max_length=128,
        verbose_name=_("name"))
    level = models.IntegerField(
        choices=LEVEL_CHOICES,
        verbose_name=_("level"),
        default=LEVEL_COUNTRY)
    parent = models.ForeignKey(
        "groups.Boundary",
        null=True,
        related_name="children",
        verbose_name=_("parent"),
        on_delete=models.SET_NULL)
    geometry = models.TextField(
        help_text=_("The GeoJSON geometry of this boundary."),
        verbose_name=_("geojson"))

    objects = BoundaryManager()

    class Meta:
        unique_together = (
            ('org', 'rapidpro_uuid'),
        )

    def __str__(self):
        return self.name

    def as_geojson(self):
        if not hasattr(self, '_geojson'):
            self._geojson = {
                'type': "Feature",
                'geometry': json.loads(self.geometry),
                'properties': {
                    'id': self.id,
                    'level': self.level,
                    'name': self.name,
                },
            }
        return self._geojson
