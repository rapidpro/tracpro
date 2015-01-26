from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.db import models
from django.utils.translation import ugettext_lazy as _
from tracpro.contacts.models import Contact


class Poll(models.Model):
    """
    Corresponds to a RapidPro Flow
    """
    flow_uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='polls')

    name = models.CharField(max_length=64, verbose_name=_("Name"))  # taken from flow name

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, org, name, flow_uuid):
        return cls.objects.create(org=org, name=name, flow_uuid=flow_uuid)

    @classmethod
    def update_flows(cls, org, flow_uuids):
        # de-activate polls whose flows were not selected
        org.polls.exclude(flow_uuid=flow_uuids).update(is_active=False)

        # fetch flow details
        flows_by_uuid = {flow.uuid: flow for flow in org.get_temba_client().get_flows()}

        for flow_uuid in flow_uuids:
            flow = flows_by_uuid[flow_uuid]

            poll = org.polls.filter(flow_uuid=flow.uuid).first()
            if poll:
                poll.name = flow.name
                poll.is_active = True
                poll.save()
            else:
                poll = cls.create(org, flow.name, flow.uuid)

            poll.update_questions_from_rulesets(flow.rulesets)

    def update_questions_from_rulesets(self, rulesets):
        # de-activate any existing questions no longer included
        self.questions.exclude(ruleset_uuid=[r.uuid for r in rulesets]).update(is_active=False)

        for ruleset in rulesets:
            question = self.questions.filter(ruleset_uuid=ruleset.uuid).first()
            if question:
                question.text = ruleset.label
                question.is_active = True
                question.save()
            else:
                Question.create(self, ruleset.label, ruleset.uuid)

    @classmethod
    def get_all(cls, org):
        return org.polls.filter(is_active=True)

    def get_questions(self):
        return self.questions.filter(is_active=True)

    def __unicode__(self):
        return self.name


class Question(models.Model):
    """
    Corresponds to RapidPro RuleSet
    """
    ruleset_uuid = models.CharField(max_length=36, unique=True)

    poll = models.ForeignKey(Poll, related_name='questions')

    text = models.CharField(max_length=64)  # taken from RuleSet label

    show_with_contact = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, poll, text, ruleset_uuid):
        return cls.objects.create(poll=poll, text=text, ruleset_uuid=ruleset_uuid)


class Issue(models.Model):
    """
    Corresponds to a RapidPro FlowStart
    """
    flow_start_id = models.IntegerField()

    poll = models.ForeignKey(Poll, related_name='issues')

    conducted_on = models.DateTimeField(help_text=_("When the poll was conducted"))

    @classmethod
    def create(cls, poll, created_on, flow_start_id):
        return cls.objects.create(poll=poll, created_on=created_on, flow_start_id=flow_start_id)


class Response(models.Model):
    """
    Corresponds to RapidPro FlowRun
    """
    flow_run_id = models.IntegerField()

    issue = models.ForeignKey(Issue, related_name='responses')

    contact = models.ForeignKey(Contact, related_name='responses')

    created_on = models.DateTimeField(help_text=_("When this response was created"))

    @classmethod
    def from_run(cls, poll, run):
        # TODO for now just get last issue
        issue = poll.issues.order_by('-conducted_on').first()

        contact = Contact.objects.filter(org=poll.org, uuid=run.contact)

        # TODO fetch and create contact if they don't exist

        response = Response.objects.create(flow_run_id=run.id, issue=issue, contact=contact, created_on=run.created_on)

        # organize values by ruleset UUID
        valuesets_by_ruleset = {valueset.node: valueset for valueset in run.values}

        # convert ruleset values to answers
        for question in poll.questions:
            valueset = valuesets_by_ruleset.get(question.ruleset_uuid, None)
            if valueset:
                Answer.objects.create(response=response, question=question,
                                      category=valueset.category, value=valueset.value, submitted_on=valueset.time)


class Answer(models.Model):
    """
    Corresponds to RapidPro FlowStep
    """
    response = models.ForeignKey(Response, related_name='answers')

    question = models.ForeignKey(Question, related_name='answers')

    category = models.CharField(max_length=36, null=True)

    value = models.CharField(max_length=640, null=True)

    submitted_on = models.DateTimeField(help_text=_("When this answer was submitted"))
