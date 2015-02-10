from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dash.utils import intersection
from dash.utils.sync import ChangeType
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from temba.types import Contact as TembaContact
from tracpro.groups.models import Region, Group
from uuid import uuid4
from .tasks import push_contact_change


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact
    """
    uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name="contacts")

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this contact"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    region = models.ForeignKey(Region, verbose_name=_("Region"), related_name='contacts',
                               help_text=_("Region or state this contact lives in"))

    group = models.ForeignKey(Group, null=True, verbose_name=_("Reporter group"), related_name='contacts')

    is_active = models.BooleanField(default=True, help_text=_("Whether this contact is active"))

    created_by = models.ForeignKey(User, null=True, related_name="contact_creations",
                                   help_text="The user which originally created this item")

    created_on = models.DateTimeField(auto_now_add=True,
                                      help_text="When this item was originally created")

    modified_by = models.ForeignKey(User, null=True, related_name="contact_modifications",
                                    help_text="The user which last modified this item")

    modified_on = models.DateTimeField(auto_now=True,
                                       help_text="When this item was last modified")

    @classmethod
    def create(cls, org, user, name, urn, region, group, uuid=None):
        if org.id != region.org_id or org.id != group.org_id:  # pragma: no cover
            raise ValueError("Region or group does not belong to org")

        # if we don't have a UUID, then we created this contact
        if not uuid:
            do_push = True
            uuid = unicode(uuid4())
        else:
            do_push = False

        # create contact
        contact = cls.objects.create(org=org, name=name, urn=urn, region=region, group=group, uuid=uuid,
                                     created_by=user, modified_by=user)

        if do_push:
            contact.push(ChangeType.created)

        return contact

    @classmethod
    def get_or_fetch(cls, org, uuid):
        """
        Gets a contact by UUID. If we don't find them locally, we try to fetch them from RapidPro
        """
        contact = Contact.objects.filter(org=org, uuid=uuid).first()
        if contact:
            return contact

        temba_contact = org.get_temba_client().get_contact(uuid)
        return cls.objects.create(**cls.kwargs_from_temba(org, temba_contact))

    @classmethod
    def get_all(cls, org):
        return org.contacts.filter(is_active=True)

    @classmethod
    def kwargs_from_temba(cls, org, temba_contact):
        org_region_uuids = [r.uuid for r in org.regions.all()]
        region_uuids = intersection(org_region_uuids, temba_contact.groups)
        region = Region.objects.get(org=org, uuid=region_uuids[0]) if region_uuids else None

        if not region:  # pragma: no cover
            raise ValueError("No region with UUID in %s" % ", ".join(temba_contact.groups))

        org_group_uuids = [g.uuid for g in org.groups.all()]
        group_uuids = intersection(org_group_uuids, temba_contact.groups)
        group = Group.objects.get(org=org, uuid=group_uuids[0]) if group_uuids else None

        return dict(org=org, name=temba_contact.name, urn=temba_contact.urns[0],
                    region=region, group=group, uuid=temba_contact.uuid)

    def as_temba(self):
        groups = [self.region.uuid]
        if self.group_id:
            groups.append(self.group.uuid)

        temba_contact = TembaContact()
        temba_contact.name = self.name
        temba_contact.urns = [self.urn]
        temba_contact.fields = {}
        temba_contact.groups = groups
        temba_contact.uuid = self.uuid
        return temba_contact

    def push(self, change_type):
        push_contact_change.delay(self.id, change_type)

    def get_urn(self):
        return tuple(self.urn.split(':', 1))

    def release(self):
        self.is_active = False
        self.save()
        self.push(ChangeType.deleted)

    def __unicode__(self):
        return self.name if self.name else self.get_urn()[1]
