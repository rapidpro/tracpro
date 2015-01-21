from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractGroup(models.Model):
    """
    Corresponds to a RapidPro contact group
    """
    uuid = models.CharField(max_length=36)

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this region"))

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name="%(class)ss")

    @classmethod
    def create(cls, org, name, uuid):
        return cls.objects.create(org=org, name=name, uuid=uuid)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class Region(AbstractGroup):
    pass


class Group(AbstractGroup):
    pass