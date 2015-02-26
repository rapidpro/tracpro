from __future__ import absolute_import, unicode_literals

import math
import operator
import pycountry
import pytz
import re
import stop_words

from collections import Counter, defaultdict, OrderedDict
from dash.orgs.models import Org
from dash.utils import get_cacheable, get_month_range
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from enum import Enum
from tracpro.contacts.models import Contact
from tracpro.groups.models import Region
from .tasks import issue_start

QUESTION_TYPE_OPEN = 'O'
QUESTION_TYPE_MULTIPLE_CHOICE = 'C'
QUESTION_TYPE_NUMERIC = 'N'

QUESTION_TYPE_CHOICES = ((QUESTION_TYPE_OPEN, _("Open Ended")),
                         (QUESTION_TYPE_MULTIPLE_CHOICE, _("Multiple Choice")),
                         (QUESTION_TYPE_NUMERIC, _("Numeric")))


UNIT_NAMES = {'d': 'days', 'm': 'months'}


class Window(Enum):
    """
    Data window
    """
    this_month = (0, 'm', _("This month"))
    last_30_days = (30, 'd', _("Last 30 days"))
    last_60_days = (60, 'd', _("Last 60 days"))
    last_90_days = (90, 'd', _("Last 90 days"))

    def __init__(self, ordinal, unit, label):
        self.ordinal = ordinal
        self.unit = unit
        self.label = label

    def to_range(self, now=None):
        if not now:
            now = timezone.now()

        if self.ordinal == 0:
            return get_month_range(now)
        else:
            since = now - relativedelta(**{UNIT_NAMES[self.unit]: self.ordinal})
            return since, now


RESPONSE_EMPTY = 'E'
RESPONSE_PARTIAL = 'P'
RESPONSE_COMPLETE = 'C'
RESPONSE_STATUS_CHOICES = ((RESPONSE_EMPTY, _("Empty")),
                           (RESPONSE_PARTIAL, _("Partial")),
                           (RESPONSE_COMPLETE, _("Complete")))

ANSWER_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week


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
        flows_by_uuid = {flow.uuid: flow for flow in org.get_temba_client().get_flows(uuids=flow_uuids)}

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

        order = 1
        for ruleset in rulesets:
            question = self.questions.filter(ruleset_uuid=ruleset.uuid).first()
            if question:
                question.text = ruleset.label
                question.type = ruleset.response_type
                question.order = order
                question.is_active = True
                question.save()
            else:
                Question.create(self, ruleset.label, ruleset.response_type, order, ruleset.uuid)
            order += 1

    @classmethod
    def get_all(cls, org):
        return org.polls.filter(is_active=True)

    def get_questions(self):
        return self.questions.filter(is_active=True).order_by('order')

    def get_issues(self, region=None):
        return Issue.get_all(self.org, region).filter(poll=self)

    def __unicode__(self):
        return self.name


class Question(models.Model):
    """
    Corresponds to RapidPro RuleSet
    """
    ruleset_uuid = models.CharField(max_length=36, unique=True)

    poll = models.ForeignKey(Poll, related_name='questions')

    text = models.CharField(max_length=64)

    type = models.CharField(max_length=1, choices=QUESTION_TYPE_CHOICES)

    order = models.IntegerField()

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, poll, text, _type, order, ruleset_uuid):
        return cls.objects.create(poll=poll, text=text, type=_type, order=order, ruleset_uuid=ruleset_uuid)


class Issue(models.Model):
    """
    Associates polls conducted on the same day
    """
    poll = models.ForeignKey(Poll, related_name='issues')

    region = models.ForeignKey(Region, null=True, related_name='issues', help_text="Region where poll was conducted")

    conducted_on = models.DateTimeField(help_text=_("When the poll was conducted"))

    created_by = models.ForeignKey(User, null=True, related_name="issues_created")

    @classmethod
    def create_regional(cls, user, poll, region, conducted_on, do_start=False):
        issue = cls.objects.create(poll=poll, region=region, conducted_on=conducted_on, created_by=user)

        if do_start:
            issue_start.delay(issue.pk)

        return issue

    @classmethod
    def get_or_create_non_regional(cls, org, poll, for_date=None):
        """
        Gets or creates an issue for a non-regional poll started in RapidPro
        """
        if not for_date:
            for_date = timezone.now()

        # get the requested date in the org timezone
        org_timezone = pytz.timezone(org.timezone)
        for_local_date = for_date.astimezone(org_timezone).date()

        # if the last non-regional issue of this poll was on same day, return that
        last = poll.issues.filter(region=None).order_by('-conducted_on').first()
        if last and last.conducted_on.astimezone(org_timezone).date() == for_local_date:
            return last

        return cls.objects.create(poll=poll, conducted_on=for_date)

    @classmethod
    def get_all(cls, org, region=None):
        issues = cls.objects.filter(poll__org=org, poll__is_active=True)

        if region:
            # any issue to this region or any non-regional issue
            issues = issues.filter(Q(region=None) | Q(region=region))

        return issues.select_related('poll', 'region')

    def get_responses(self, region=None, include_empty=True):
        if region and self.region_id and region.pk != self.region_id:
            raise ValueError("Request for responses in region where poll wasn't conducted")

        responses = self.responses.filter(is_active=True)
        if region:
            responses = responses.filter(contact__region=region)
        if not include_empty:
            responses = responses.exclude(status=RESPONSE_EMPTY)

        return responses.select_related('contact')

    def get_response_counts(self, region=None):
        status_counts = self.get_responses(region).values('status').annotate(count=Count('status'))

        base = {RESPONSE_EMPTY: 0, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 0}
        base.update({sc['status']: sc['count'] for sc in status_counts})
        return base

    def is_last_for_region(self, region):
        """
        Whether or not this is the last issue of the poll conducted in the given region. Includes non-regional polls.
        """
        # did this issue cover the given region
        if self.region_id and self.region_id != region.pk:
            return False

        # did any newer issues cover the given region
        newer_issues = Issue.objects.filter(poll=self.poll, pk__gt=self.pk)
        newer_issues = newer_issues.filter(Q(region=None) | Q(region=region))
        return not newer_issues.exists()

    def get_answers_to(self, question, region=None):
        """
        Gets all answers from active responses for this issue, to the given question
        """
        qs = Answer.objects.filter(response__issue=self, response__is_active=True, question=question)
        if region:
            qs = qs.filter(response__contact__region=region)

        return qs.select_related('response__contact')

    def get_answer_aggregates(self, question, region=None):
        def calculate():
            if question.type == QUESTION_TYPE_OPEN:
                return self.calculate_answer_word_counts(question, region)
            elif question.type == QUESTION_TYPE_MULTIPLE_CHOICE:
                return self.calculate_answer_category_counts(question, region)
            elif question.type == QUESTION_TYPE_NUMERIC:
                return self.calculate_answer_numeric_counts(question, region)
            else:
                return []

        cache_key = self._answer_cache_key(question, region)
        return get_cacheable(cache_key, ANSWER_CACHE_TTL, calculate)

    def calculate_answer_word_counts(self, question, region=None):
        answers = self.get_answers_to(question, region)
        word_counts = defaultdict(int)
        for answer in answers:
            contact = answer.response.contact
            for w in extract_words(answer.value, contact.language):
                word_counts[w] += 1

        sorted_counts = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_counts[:50]  # only return top 50

    def calculate_answer_category_counts(self, question, region=None):
        answers = self.get_answers_to(question, region)
        category_counts = Counter([answer.category for answer in answers])
        return sorted(category_counts.items(), key=operator.itemgetter(1), reverse=True)

    def calculate_answer_numeric_counts(self, question, region=None):
        answers = self.get_answers_to(question, region)
        return auto_categorize_numbers([answer.value for answer in answers], 5).items()

    def clear_answer_cache(self, question, region):
        """
        Clears an answer cache for this issue for the given region and the non-regional (0) cache
        """
        # always clear the non-regional cache
        cache.delete(self._answer_cache_key(question, None))
        if region:
            cache.delete(self._answer_cache_key(question, region))

    def _answer_cache_key(self, question, region):
        region_id = region.pk if region else 0
        return 'issue:%d:answer_cache:%d:%d' % (self.pk, question.pk, region_id)

    def as_json(self, region=None):
        region_as_json = dict(id=self.region.pk, name=self.region.name) if self.region else None

        return dict(id=self.pk,
                    poll=dict(id=self.poll.pk, name=self.poll.name),
                    conducted_on=self.conducted_on,
                    region=region_as_json,
                    responses=self.get_response_counts(region))

    def __unicode__(self):
        return "%s (%s)" % (self.poll.name, self.conducted_on.strftime(settings.SITE_DATE_FORMAT))


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
    def create_empty(cls, org, issue, run):
        """
        Creates an empty response from a run. Used to start or restart a contact in an existing issue.
        """
        contact = Contact.get_or_fetch(org, uuid=run.contact)

        # de-activate any existing responses for this contact
        issue.responses.filter(contact=contact).update(is_active=False)

        return Response.objects.create(flow_run_id=run.id, issue=issue, contact=contact,
                                       created_on=run.created_on, updated_on=run.created_on,
                                       status=RESPONSE_EMPTY)

    @classmethod
    def from_run(cls, org, run, poll=None):
        """
        Gets or creates a response from a flow run. If response is not up-to-date with provided run, then it is
        updated. If the run doesn't match with an existing poll issue, it's assumed to be non-regional.
        """
        response = Response.objects.filter(issue__poll__org=org, flow_run_id=run.id).select_related('issue').first()
        run_updated_on = cls.get_run_updated_on(run)

        # if there is an up-to-date existing response for this run, return it
        if response and response.updated_on == run_updated_on:
            return response

        if not poll:
            poll = Poll.get_all(org).get(flow_uuid=run.flow)

        contact = Contact.get_or_fetch(poll.org, uuid=run.contact)

        # categorize completeness
        if run.completed:
            status = RESPONSE_COMPLETE
        elif run.values:
            status = RESPONSE_PARTIAL
        else:
            status = RESPONSE_EMPTY

        if response:
            # clear existing answers which will be replaced
            response.answers.all().delete()

            response.updated_on = run_updated_on
            response.status = status
            response.save(update_fields=('updated_on', 'status'))
        else:
            # if we don't have an existing response, then this poll started in RapidPro and is non-regional
            issue = Issue.get_or_create_non_regional(org, poll, for_date=run.created_on)

            # if contact has an older response for this issue, retire it
            Response.objects.filter(issue=issue, contact=contact).update(is_active=False)

            response = Response.objects.create(flow_run_id=run.id, issue=issue, contact=contact,
                                               created_on=run.created_on, updated_on=run_updated_on,
                                               status=status)
            response.is_new = True

        # organize values by ruleset UUID
        questions = poll.get_questions()
        valuesets_by_ruleset = {valueset.node: valueset for valueset in run.values}
        valuesets_by_question = {q: valuesets_by_ruleset.get(q.ruleset_uuid, None) for q in questions}

        # convert valuesets to answers
        for question, valueset in valuesets_by_question.iteritems():
            if valueset:
                Answer.create(response, question, valueset.value, valueset.category, valueset.time)

        # clear answer caches for this contact's region
        for question in questions:
            response.issue.clear_answer_cache(question, contact.region)

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
        # category can be a string or a multi-language dict
        if isinstance(category, dict):
            if 'base' in category:
                category = category['base']
            else:
                category = category.itervalues().next()

        return Answer.objects.create(response=response, question=question,
                                     value=value, category=category, submitted_on=submitted_on)


def get_stop_words(iso_code):
    code = pycountry.languages.get(bibliographic=iso_code).alpha2
    try:
        return stop_words.get_stop_words(code)
    except stop_words.StopWordError:
        return []


def extract_words(text, language):
    """
    Extracts significant words from the given text (i.e. words we want to include in a word cloud)
    """
    words = re.split(r"[^\w'-]", text.lower(), flags=re.UNICODE)
    ignore_words = get_stop_words(language) if language else []
    return [w for w in words if w not in ignore_words and len(w) > 1]


def auto_categorize_numbers(raw_values, num_categories):
    """
    Creates automatic range categories for a given set of numbers and returns the count of values in each category
    """
    if not raw_values:
        return {}

    # convert to integers and find minimum and maximum
    values = []
    value_min = None
    value_max = None
    for value in raw_values:
        try:
            value = int(Decimal(value))
            if value < value_min or value_min is None:
                value_min = value
            if value > value_max or value_max is None:
                value_max = value
            values.append(value)
        except ValueError:
            continue

    # pick best fitting categories
    value_range = value_max - value_min
    category_step = int(math.ceil(float(value_range) / num_categories)) if value_range else 1
    category_range = category_step * num_categories
    category_min = value_min - (category_range - value_range) / 2

    # don't start categories in negative if min value isn't negative
    if category_min < 0 and not value_min < 0:
        category_min = 0

    # create category labels and initialize counts
    category_counts = OrderedDict()
    category_labels = {}

    for cat in range(0, num_categories):
        cat_min = category_min + cat * category_step
        if category_step > 1:
            cat_max = (category_min + (cat + 1) * category_step) - 1
            cat_label = '%d - %d' % (cat_min, cat_max)
        else:
            cat_label = unicode(cat_min)

        category_labels[cat] = cat_label
        category_counts[cat_label] = 0

    # count categorized values
    for value in values:
        category = int(num_categories * (value - category_min) / category_range)
        label = category_labels[category]
        category_counts[label] += 1

    return category_counts
