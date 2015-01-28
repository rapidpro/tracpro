from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
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
    def get_all(cls, org):
        return cls.objects.filter(org=org, is_active=True)

    def get_contacts(self):
        return self.contacts.filter(is_active=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class Region(AbstractGroup):
    users = models.ManyToManyField(User, verbose_name=_("Users"), related_name='regions',
                                   help_text=_("Users who can access this region"))

    @classmethod
    def sync_with_groups(cls, org, group_uuids):
        """
        Updates an org's regions based on the selected groups UUIDs
        """
        # de-activate regions not included
        org.regions.exclude(uuid__in=group_uuids).update(is_active=False)

        # fetch group details
        groups = org.get_temba_client().get_groups()
        group_names = {group.uuid: group.name for group in groups}

        for group_uuid in group_uuids:
            existing = org.regions.filter(uuid=group_uuid).first()
            if existing:
                existing.name = group_names[group_uuid]
                existing.is_active = True
                existing.save()
            else:
                cls.create(org, group_names[group_uuid], group_uuid)

        sync_org_contacts.delay(org.id)

    def get_users(self):
        return self.users.filter(is_active=True).select_related('profile')


class Group(AbstractGroup):
    @classmethod
    def sync_with_groups(cls, org, group_uuids):
        """
        Updates an org's reporter groups based on the selected groups UUIDs
        """
        # de-activate groups not included
        org.groups.exclude(uuid__in=group_uuids).update(is_active=False)

        # fetch group details
        groups = org.get_temba_client().get_groups()
        group_names = {group.uuid: group.name for group in groups}

        for group_uuid in group_uuids:
            existing = org.groups.filter(uuid=group_uuid).first()
            if existing:
                existing.name = group_names[group_uuid]
                existing.is_active = True
                existing.save()
            else:
                cls.create(org, group_names[group_uuid], group_uuid)