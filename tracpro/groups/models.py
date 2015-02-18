from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from tracpro.contacts.tasks import sync_org_contacts


class AbstractGroup(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name="%(class)ss")

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this region"))

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, org, name, uuid):
        return cls.objects.create(org=org, name=name, uuid=uuid)

    @classmethod
    def sync_with_groups(cls, org, group_uuids):
        """
        Updates an org's groups based on the selected groups UUIDs
        """
        # de-activate any active groups not included
        cls.objects.filter(org=org, is_active=True).exclude(uuid__in=group_uuids).update(is_active=False)

        # fetch group details
        groups = org.get_temba_client().get_groups()
        group_names = {group.uuid: group.name for group in groups}

        for group_uuid in group_uuids:
            existing = cls.objects.filter(org=org, uuid=group_uuid).first()
            if existing:
                existing.name = group_names[group_uuid]
                existing.is_active = True
                existing.save()
            else:
                cls.create(org, group_names[group_uuid], group_uuid)

    @classmethod
    def get_all(cls, org):
        return cls.objects.filter(org=org, is_active=True)

    @classmethod
    def get_response_counts(cls, org, window=None, include_empty=False):
        from tracpro.polls.models import Response, RESPONSE_EMPTY
        qs = Response.objects.filter(issue__poll__org=org, is_active=True)

        if not include_empty:
            qs = qs.exclude(status=RESPONSE_EMPTY)

        if window:
            window_min, window_max = window.to_range()
            qs = qs.filter(updated_on__gte=window_min, updated_on__lt=window_max)

        field = 'contact__%s' % cls.__name__.lower()

        qs = qs.filter(**{'%s__is_active' % field: True})
        counts = qs.values(field).annotate(count=Count(field))
        return {count[field]: count['count'] for count in counts}

    @classmethod
    def get_most_active(cls, org):
        from tracpro.polls.models import Window

        count_by_id = cls.get_response_counts(org, window=Window.last_30_days, include_empty=False)

        groups = []
        for group in cls.get_all(org):
            count = count_by_id.get(group.pk, 0)
            if count:
                group.response_count = count
                groups.append(group)

        return sorted(groups, key=lambda g: g.response_count, reverse=True)

    def get_contacts(self):
        return self.contacts.filter(is_active=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class Region(AbstractGroup):
    """
    A geographical region modelled as a group
    """
    users = models.ManyToManyField(User, verbose_name=_("Users"), related_name='regions',
                                   help_text=_("Users who can access this region"))

    @classmethod
    def sync_with_groups(cls, org, group_uuids):
        """
        Updates an org's regions based on the selected groups UUIDs
        """
        super(Region, cls).sync_with_groups(org, group_uuids)

        sync_org_contacts.delay(org.id)

    def get_users(self):
        return self.users.filter(is_active=True).select_related('profile')


class Group(AbstractGroup):
    """
    A data reporting group
    """
    pass