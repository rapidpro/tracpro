from __future__ import absolute_import, unicode_literals

import pytz

from dash.orgs.models import Org
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from tracpro.contacts.models import Contact
from tracpro.groups.models import Region


RESPONSE_EMPTY = 'E'
RESPONSE_PARTIAL = 'P'
RESPONSE_COMPLETE = 'C'
RESPONSE_STATUS_CHOICES = ((RESPONSE_EMPTY, _("Empty")),
                           (RESPONSE_PARTIAL, _("Partial")),
                           (RESPONSE_COMPLETE, _("Complete")))


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
    def sync_with_flows(cls, org, flow_uuids):
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

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, poll, text, ruleset_uuid):
        return cls.objects.create(poll=poll, text=text, ruleset_uuid=ruleset_uuid)


class Issue(models.Model):
    """
    Associates polls conducted on the same day
    """
    poll = models.ForeignKey(Poll, related_name='issues')

    # TODO change this to be ForeignKey so polls go to one region or all
    regions = models.ManyToManyField(Region, related_name='issues', help_text="Regions where poll was conducted")

    conducted_on = models.DateTimeField(help_text=_("When the poll was conducted"))

    @classmethod
    def create(cls, poll, regions, conducted_on):
        issue = cls.objects.create(poll=poll, conducted_on=conducted_on)
        for region in regions:
            issue.regions.add(region)
        return issue

    @classmethod
    def get_or_create(cls, org, poll, region, for_date=None):
        if not for_date:
            for_date = timezone.now()

        # get the requested date in the org timezone
        org_timezone = pytz.timezone(org.timezone)
        for_local_date = for_date.astimezone(org_timezone).date()

        # if the last issue of this poll to this region was on same day, return that
        last = region.issues.order_by('-conducted_on').first()
        if last and last.conducted_on.astimezone(org_timezone).date() == for_local_date:
            return last

        return Issue.create(poll, [region], for_date)

    @classmethod
    def get_all(cls, org):
        return cls.objects.filter(poll__org=org, poll__is_active=True)

    def get_responses(self, region=None):
        responses = self.responses.filter(is_active=True)
        if region:
            responses = responses.filter(contact__region=region)

        return responses.select_related('contact')

    def get_complete_responses(self, region=None):
        return self.get_responses(region).filter(status=RESPONSE_COMPLETE)

    def get_incomplete_responses(self, region=None):
        return self.get_responses(region).exclude(status=RESPONSE_COMPLETE)

    def get_completion(self, region=None):
        """
        Gets the completion level for this issue. An issue with no responses (complete or incomplete) returns None
        """
        total_responses = self.get_responses(region).count()
        if total_responses:
            return self.get_complete_responses(region).count() / float(total_responses)
        else:
            return None

    def __unicode__(self):
        return "%s (%s)" % (self.poll.name, self.conducted_on.strftime("%b %d, %Y"))


class Response(models.Model):
    """
    Corresponds to RapidPro FlowRun
    """
    flow_run_id = models.IntegerField(unique=True)

    issue = models.ForeignKey(Issue, related_name='responses')

    contact = models.ForeignKey(Contact, related_name='responses')

    created_on = models.DateTimeField(help_text=_("When this response was created"))

    updated_on = models.DateTimeField(help_text=_("When the last activity on this response was"))

    status = models.CharField(max_length=1, verbose_name=_("Status"), choices=RESPONSE_STATUS_CHOICES,
                              help_text=_("Current status of this response"))

    is_active = models.BooleanField(default=True, help_text="Whether this response is active")

    @classmethod
    def get_or_create(cls, org, run, poll=None):
        """
        Gets or creates a response from a Temba flow run. If response is not up-to-date with provided run, then it is
        updated.
        """
        response = Response.objects.filter(issue__poll__org=org, flow_run_id=run.id).first()
        run_updated_on = cls.get_run_updated_on(run)

        # if there is an up-to-date existing response for this run, return it
        if response and response.updated_on == run_updated_on:
            return response

        if not poll:
            poll = Poll.get_all(org).get(flow_uuid=run.flow)

        contact = Contact.get_or_fetch(poll.org, uuid=run.contact)
        issue = Issue.get_or_create(org, poll, contact.region)

        # if contact has an older response for this issue, retire it
        Response.objects.filter(issue=issue, contact=contact).update(is_active=False)

        # organize values by ruleset UUID
        questions = poll.get_questions()
        valuesets_by_ruleset = {valueset.node: valueset for valueset in run.values}
        valuesets_by_question = {q: valuesets_by_ruleset.get(q.ruleset_uuid, None) for q in questions}

        completed_questions = sum(1 for v in valuesets_by_question.values() if v is not None)
        if completed_questions == 0:
            status = RESPONSE_EMPTY
        elif completed_questions < len(questions):
            status = RESPONSE_PARTIAL
        else:
            status = RESPONSE_COMPLETE

        if response:
            # clear existing answers which will be replaced
            response.answers.all().delete()

            response.updated_on = run_updated_on
            response.status = status
            response.save(update_fields=('updated_on', 'status'))
        else:
            response = Response.objects.create(flow_run_id=run.id, issue=issue, contact=contact,
                                               created_on=run.created_on, updated_on=run_updated_on,
                                               status=status)

        # convert valuesets to answers
        for question, valueset in valuesets_by_question.iteritems():
            if valueset:
                Answer.create(response, question, valueset.value, valueset.category, valueset.time)

        return response

    @classmethod
    def get_run_updated_on(cls, run):
        # find the valueset with the latest time
        last_value_on = None
        for valueset in run.values:
            if not last_value_on or valueset.time > last_value_on:
                last_value_on = valueset.time

        return last_value_on if last_value_on else run.created_on

    @classmethod
    def get_update_required(cls, org):
        """
        Gets incomplete responses to the latest issues of all polls so that they can be updated
        """
        # get polls with the latest issue id for each
        polls = Poll.get_all(org).annotate(latest_issue_id=models.Max('issues'))
        latest_issues = [p.latest_issue_id for p in polls if p.latest_issue_id]

        return Response.objects.filter(issue__in=latest_issues, is_active=True).exclude(status=RESPONSE_COMPLETE)


class Answer(models.Model):
    """
    Corresponds to RapidPro FlowStep
    """
    response = models.ForeignKey(Response, related_name='answers')

    question = models.ForeignKey(Question, related_name='answers')

    value = models.CharField(max_length=640, null=True)

    category = models.CharField(max_length=36, null=True)

    submitted_on = models.DateTimeField(help_text=_("When this answer was submitted"))

    @classmethod
    def create(cls, response, question, value, category, submitted_on):
        return Answer.objects.create(response=response, question=question,
                                     value=value, category=category, submitted_on=submitted_on)
