from __future__ import absolute_import, unicode_literals

from dateutil.relativedelta import relativedelta

from mptt import models as mptt

from django.conf import settings
from django.db import models, transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.contacts.tasks import SyncOrgContacts


@python_2_unicode_compatible
class AbstractGroup(models.Model):
    """Corresponds to a RapidPro contact group."""

    uuid = models.CharField(max_length=36, unique=True)
    org = models.ForeignKey(
        'orgs.Org', verbose_name=_("Organization"), related_name="%(class)ss")
    name = models.CharField(
        verbose_name=_("Name"), max_length=128, blank=True,
        help_text=_("The name of this region"))
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this item is active"))

    class Meta:
        abstract = True

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
        temba_groups = org.get_temba_client().get_groups()
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
        help_text=_("Users who can access this region"))
    parent = mptt.TreeForeignKey(
        'self', null=True, blank=True, related_name="children", db_index=True)

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
    pass
