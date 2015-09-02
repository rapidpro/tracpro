from __future__ import absolute_import, unicode_literals

from collections import Counter, defaultdict, OrderedDict
from decimal import Decimal, InvalidOperation
import operator

from dateutil.relativedelta import relativedelta
from enum import Enum
import pytz

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from dash.utils import get_cacheable, get_month_range

from tracpro.contacts.models import Contact

from .tasks import pollrun_start
from .utils import auto_range_categories, extract_words


QUESTION_TYPE_OPEN = 'O'
QUESTION_TYPE_MULTIPLE_CHOICE = 'C'
QUESTION_TYPE_NUMERIC = 'N'
QUESTION_TYPE_MENU = 'M'
QUESTION_TYPE_KEYPAD = 'K'
QUESTION_TYPE_RECORDING = 'R'

QUESTION_TYPE_CHOICES = ((QUESTION_TYPE_OPEN, _("Open Ended")),
                         (QUESTION_TYPE_MULTIPLE_CHOICE, _("Multiple Choice")),
                         (QUESTION_TYPE_NUMERIC, _("Numeric")),
                         (QUESTION_TYPE_MENU, _("Menu")),
                         (QUESTION_TYPE_KEYPAD, _("Keypad")),
                         (QUESTION_TYPE_RECORDING, _("Recording")))


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


class AnswerCache(Enum):
    word_counts = 1
    category_counts = 2
    range_counts = 3
    average = 4


ANSWER_CACHE_KEY = 'pollrun:%d:question:%d:%s:%d'
ANSWER_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week


@python_2_unicode_compatible
class Poll(models.Model):
    """
    Corresponds to a RapidPro Flow
    """
    flow_uuid = models.CharField(max_length=36, unique=True)

    org = models.ForeignKey('orgs.Org', verbose_name=_("Organization"), related_name='polls')

    name = models.CharField(max_length=64, verbose_name=_("Name"))  # taken from flow name

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    def __str__(self):
        return self.name

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

    def get_pollruns(self, region=None):
        return PollRun.get_all(self.org, region).filter(poll=self)


class Question(models.Model):
    """
    Corresponds to RapidPro RuleSet
    """
    ruleset_uuid = models.CharField(max_length=36, unique=True)

    poll = models.ForeignKey('polls.Poll', related_name='questions')

    text = models.CharField(max_length=64)

    type = models.CharField(max_length=1, choices=QUESTION_TYPE_CHOICES)

    order = models.IntegerField()

    is_active = models.BooleanField(default=True, help_text="Whether this item is active")

    @classmethod
    def create(cls, poll, text, _type, order, ruleset_uuid):
        return cls.objects.create(poll=poll, text=text, type=_type, order=order, ruleset_uuid=ruleset_uuid)

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class PollRun(models.Model):
    """
    Associates polls conducted on the same day
    """
    poll = models.ForeignKey('polls.Poll', related_name='pollruns')

    region = models.ForeignKey(
        'groups.Region', null=True, related_name='pollruns',
        help_text="Region where poll was conducted")

    conducted_on = models.DateTimeField(help_text=_("When the poll was conducted"))

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name="pollruns_created")

    def __str__(self):
        return "%s (%s)" % (self.poll.name, self.conducted_on.strftime(settings.SITE_DATE_FORMAT))

    @classmethod
    def create_regional(cls, user, poll, region, conducted_on, do_start=False):
        pollrun = cls.objects.create(poll=poll, region=region, conducted_on=conducted_on, created_by=user)

        if do_start:
            pollrun_start.delay(pollrun.pk)

        return pollrun

    @classmethod
    def get_or_create_non_regional(cls, org, poll, for_date=None):
        """
        Gets or creates an pollrun for a non-regional poll started in RapidPro
        """
        if not for_date:
            for_date = timezone.now()

        # get the requested date in the org timezone
        org_timezone = pytz.timezone(org.timezone)
        for_local_date = for_date.astimezone(org_timezone).date()

        # look for a non-regional pollrun on that date
        sql = ('SELECT * FROM polls_pollrun WHERE poll_id = %s AND '
               'region_id IS NULL AND DATE(conducted_on AT TIME ZONE %s) = %s')
        params = [poll.pk, org_timezone.zone, for_local_date]
        existing = list(PollRun.objects.raw(sql, params))

        if existing:
            return existing[0]

        return cls.objects.create(poll=poll, conducted_on=for_date)

    @classmethod
    def get_all(cls, org, region=None):
        pollruns = cls.objects.filter(poll__org=org, poll__is_active=True)

        if region:
            # any pollrun to this region or any non-regional pollrun
            pollruns = pollruns.filter(Q(region=None) | Q(region=region))

        return pollruns.select_related('poll', 'region')

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
        Whether or not this is the last pollrun of the poll conducted in the given region. Includes non-regional polls.
        """
        # did this pollrun cover the given region
        if self.region_id and self.region_id != region.pk:
            return False

        # did any newer pollruns cover the given region
        newer_pollruns = PollRun.objects.filter(poll=self.poll, pk__gt=self.pk)
        newer_pollruns = newer_pollruns.filter(Q(region=None) | Q(region=region))
        return not newer_pollruns.exists()

    def get_answers_to(self, question, region=None):
        """
        Gets all answers from active responses for this pollrun, to the given question
        """
        qs = Answer.objects.filter(response__pollrun=self, response__is_active=True, question=question)
        if region:
            qs = qs.filter(response__contact__region=region)

        return qs.select_related('response__contact')

    def get_answer_word_counts(self, question, region=None):
        """
        Gets word counts for answers to the given question, sorted from most frequent, e.g.
            [("zombies", 2), ("floods", 1)]
        """
        def calculate():
            return Answer.word_counts(self.get_answers_to(question, region))

        cache_key = self._answer_cache_key(question, AnswerCache.word_counts, region)
        return get_cacheable(cache_key, ANSWER_CACHE_TTL, calculate)

    def get_answer_category_counts(self, question, region=None):
        """
        Gets category counts for answers to the given question, sorted from most frequent, e.g.
            [("Rainy", 2), ("Sunny", 1)]
        """
        def calculate():
            return Answer.category_counts(self.get_answers_to(question, region))

        cache_key = self._answer_cache_key(question, AnswerCache.category_counts, region)
        return get_cacheable(cache_key, ANSWER_CACHE_TTL, calculate)

    def get_answer_auto_range_counts(self, question, region=None):
        """
        Gets automatic numeric range counts for answers to the given question, sorted from most frequent, e.g.
            [("0 - 9", 2), ("10 - 19", 1)]
        """
        def calculate():
            return Answer.auto_range_counts(self.get_answers_to(question, region)).items()

        cache_key = self._answer_cache_key(question, AnswerCache.range_counts, region)
        return get_cacheable(cache_key, ANSWER_CACHE_TTL, calculate)

    def get_answer_numeric_average(self, question, region=None):
        """
        Gets the numeric average of answers to the given question
        """
        def calculate():
            return Answer.numeric_average(self.get_answers_to(question, region))

        cache_key = self._answer_cache_key(question, AnswerCache.average, region)
        return get_cacheable(cache_key, ANSWER_CACHE_TTL, calculate)

    def clear_answer_cache(self, question, region):
        """
        Clears all answer cache for the given question for the given region and the non-regional (0) cache
        """
        for item in AnswerCache.__members__.values():
            # always clear the non-regional cache
            cache.delete(self._answer_cache_key(question, item, None))
            if region:
                cache.delete(self._answer_cache_key(question, item, region))

    def _answer_cache_key(self, question, item, region):
        region_id = region.pk if region else 0
        return ANSWER_CACHE_KEY % (self.pk, question.pk, item.name, region_id)

    def as_json(self, region=None):
        region_as_json = dict(id=self.region.pk, name=self.region.name) if self.region else None

        return dict(id=self.pk,
                    poll=dict(id=self.poll.pk, name=self.poll.name),
                    conducted_on=self.conducted_on,
                    region=region_as_json,
                    responses=self.get_response_counts(region))


class Response(models.Model):
    """
    Corresponds to RapidPro FlowRun
    """
    flow_run_id = models.IntegerField(unique=True, null=True)

    pollrun = models.ForeignKey('polls.PollRun', null=True, related_name='responses')

    contact = models.ForeignKey('contacts.Contact', related_name='responses')

    created_on = models.DateTimeField(help_text=_("When this response was created"))

    updated_on = models.DateTimeField(help_text=_("When the last activity on this response was"))

    status = models.CharField(max_length=1, verbose_name=_("Status"), choices=RESPONSE_STATUS_CHOICES,
                              help_text=_("Current status of this response"))

    is_active = models.BooleanField(default=True, help_text="Whether this response is active")

    @classmethod
    def create_empty(cls, org, pollrun, run):
        """
        Creates an empty response from a run. Used to start or restart a contact in an existing pollrun.
        """
        contact = Contact.get_or_fetch(org, uuid=run.contact)

        # de-activate any existing responses for this contact
        pollrun.responses.filter(contact=contact).update(is_active=False)

        return Response.objects.create(flow_run_id=run.id, pollrun=pollrun, contact=contact,
                                       created_on=run.created_on, updated_on=run.created_on,
                                       status=RESPONSE_EMPTY)

    @classmethod
    def from_run(cls, org, run, poll=None):
        """
        Gets or creates a response from a flow run. If response is not up-to-date with provided run, then it is
        updated. If the run doesn't match with an existing poll pollrun, it's assumed to be non-regional.
        """
        response = Response.objects.filter(pollrun__poll__org=org, flow_run_id=run.id).select_related('pollrun').first()
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
            pollrun = PollRun.get_or_create_non_regional(org, poll, for_date=run.created_on)

            # if contact has an older response for this pollrun, retire it
            Response.objects.filter(pollrun=pollrun, contact=contact).update(is_active=False)

            response = Response.objects.create(flow_run_id=run.id, pollrun=pollrun, contact=contact,
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
            response.pollrun.clear_answer_cache(question, contact.region)

        return response

    @classmethod
    def get_run_updated_on(cls, run):
        # find the valueset with the latest time
        last_value_on = None
        for valueset in run.values:
            if not last_value_on or valueset.time > last_value_on:
                last_value_on = valueset.time

        return last_value_on if last_value_on else run.created_on


class Answer(models.Model):
    """
    Corresponds to RapidPro FlowStep
    """
    response = models.ForeignKey('polls.Response', related_name='answers')

    question = models.ForeignKey('polls.Question', related_name='answers')

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

        if category == 'All Responses':
            category = None

        return Answer.objects.create(response=response, question=question,
                                     value=value, category=category, submitted_on=submitted_on)

    @classmethod
    def word_counts(cls, answers):
        word_counts = defaultdict(int)
        for answer in answers:
            contact = answer.response.contact
            for w in extract_words(answer.value, contact.language):
                word_counts[w] += 1

        sorted_counts = sorted(word_counts.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_counts[:50]  # only return top 50

    @classmethod
    def category_counts(cls, answers):
        category_counts = Counter([answer.category for answer in answers if answer.category])
        return sorted(category_counts.items(), key=operator.itemgetter(1), reverse=True)

    @classmethod
    def numeric_average(cls, answers):
        """
        Parses decimals out of a set of answers and returns the average. Returns zero if no valid numbers are found.
        """
        total = Decimal(0)
        count = 0
        for answer in answers:
            if answer.category is not None:  # ignore answers with no category as they weren't in the required range
                try:
                    value = Decimal(answer.value)
                    total += value
                    count += 1
                except (TypeError, ValueError, InvalidOperation):
                    continue

        return float(total / count) if count else 0

    @classmethod
    def numeric_sum_group_by_date(cls, answers):
        """
        Parses decimals out of a set of answers and returns the sum for each distinct date.
        Returns:
        answer_sums: list of sum of each value on each date ie. [33, 40, ...]
        dates: list of distinct dates ie. [datetime.date(2015, 8, 12),...]
        """
        answer_sums = []
        dates = []
        total = Decimal(0)
        answer_date = ""
        answers = answers.order_by('submitted_on')
        for answer in answers:
            if answer.category is not None:  # ignore answers with no category as they weren't in the required range
                if answer_date != answer.submitted_on.date():
                    # Append the sum total value for each date
                    if total:
                        answer_sums.append(total)
                        dates.append(answer_date)
                    answer_date = answer.submitted_on.date()
                    total = Decimal(0)
                try:
                    total += Decimal(answer.value)
                except (TypeError, ValueError, InvalidOperation):
                    continue
        # One last value to append, for the final date
        if total:
            answer_sums.append(total)
            dates.append(answer_date)
        return answer_sums, dates

    @classmethod
    def numeric_sum_all_dates(cls, answers):
        """
        Parses decimals out of a set of answers and returns the sum for all answers,
        regardless of dates.
        Returns:
        total: total sum of all answer values
        """
        total = Decimal(0)
        for answer in answers:
            if answer.category is not None:  # ignore answers with no category as they weren't in the required range
                try:
                    total += Decimal(answer.value)
                except (TypeError, ValueError, InvalidOperation):
                    continue
        return total

    @classmethod
    def auto_range_counts(cls, answers):
        """
        Creates automatic range "categories" for a given set of answers and returns the count of values in each range
        """
        # convert to integers and find minimum and maximum
        values = []
        value_min = None
        value_max = None
        for answer in answers:
            if answer.category is not None:  # ignore answers with no category as they weren't in the required range
                try:
                    value = int(Decimal(answer.value))
                    if value < value_min or value_min is None:
                        value_min = value
                    if value > value_max or value_max is None:
                        value_max = value
                    values.append(value)
                except (TypeError, ValueError, InvalidOperation):
                    continue

        if not values:
            return {}

        # pick best fitting categories
        category_min, category_max, category_step = auto_range_categories(value_min, value_max)

        # create category labels and initialize counts
        category_counts = OrderedDict()
        category_labels = {}

        cat_index = 0
        for cat_min in range(category_min, category_max, category_step):
            if category_step > 1:
                cat_max = cat_min + category_step - 1
                cat_label = '%d - %d' % (cat_min, cat_max)
            else:
                cat_label = str(cat_min)

            category_labels[cat_index] = cat_label
            category_counts[cat_label] = 0
            cat_index += 1

        # count categorized values
        for value in values:
            category = int((value - category_min) / category_step)
            label = category_labels[category]
            category_counts[label] += 1

        return category_counts
