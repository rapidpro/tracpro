from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.db import models
from django.utils.translation import ugettext_lazy as _
from tracpro.contacts.models import Contact


class Poll(models.Model):
    """
    Corresponds to a RapidPro Flow
    """
    flow_uuid = models.CharField(max_length=36)  # TODO needs added on Temba side

    name = models.CharField(max_length=64, verbose_name=_("Name of this poll"))  # taken from flow name

    org = models.ForeignKey(Org, related_name='polls')

    @classmethod
    def create(cls, org, flow_uuid, name, created_on, questions=()):
        poll = Poll.objects.create(flow_uuid=flow_uuid, name=name, org=org, created_on=created_on)
        poll.questions.add(*questions)
        return poll


class PollQuestion(models.Model):
    """
    Corresponds to RapidPro RuleSet
    """
    rule_set_uuid = models.CharField(max_length=36)

    poll = models.ForeignKey(Poll, related_name='questions')

    name = models.CharField(max_length=64)  # taken from RuleSet label

    show_with_contact = models.BooleanField(default=False)


class PollIssue(models.Model):
    """
    Corresponds to a RapidPro FlowStart
    """
    flow_start_uuid = models.CharField(max_length=36)  # TODO needs added on Temba side

    poll = models.ForeignKey(Org, related_name='starts')

    created_on = models.DateTimeField(help_text=_("When this poll was created"))


class PollResponse(models.Model):
    """
    Corresponds to RapidPro FlowRun
    """
    flow_run_uuid = models.CharField(max_length=36)  # TODO needs added on Temba side

    issue = models.ForeignKey(PollIssue, related_name='responses')

    contact = models.ForeignKey(Contact, related_name='responses')


class PollAnswer(models.Model):
    """
    Corresponds to RapidPro FlowStep
    """
    flow_step_uuid = models.CharField(max_length=36)

    response = models.ForeignKey(PollResponse, related_name='answers')

    question = models.ForeignKey(PollQuestion, related_name='answers')

    category = models.CharField(max_length=36, null=True)

    value = models.CharField(max_length=640, null=True)

    decimal_value = models.DecimalField(max_digits=36, decimal_places=8, null=True)

    submitted_on = models.DateTimeField(help_text=_("When this answer was submitted"))
