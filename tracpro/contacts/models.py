from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from tracpro.groups.models import Region, Group


class Contact(models.Model):
    """
    Corresponds to a RapidPro contact
    """
    uuid = models.CharField(max_length=36)

    name = models.CharField(verbose_name=_("Name"), max_length=128, blank=True,
                            help_text=_("The name of this contact"))

    urn = models.CharField(verbose_name=_("URN"), max_length=255)

    region = models.ForeignKey(Region, verbose_name=_("Region"), related_name='contacts',
                               help_text=_("Region or state this contact lives in"))

    group = models.ForeignKey(Group, verbose_name=_("Reporter group"), related_name='contacts')

    @classmethod
    def create(cls, name, urn, region, uuid):
        return cls.objects.create(name=name, urn=urn, region=region, uuid=uuid)

    def get_urn(self):
        return tuple(self.urn.split(':', 1))

    def get_responses(self):
        return self.responses.order_by('-created_on')

    def get_last_answer(self, question):
        from tracpro.polls.models import PollAnswer
        return PollAnswer.objects.filter(question=question, reponse__contact=self).order_by('-submitted_on').first()

    def __unicode__(self):
        return self.name if self.name else self.get_urn()[1]