from __future__ import absolute_import, unicode_literals

from collections import Counter
from itertools import chain, groupby
import json
from operator import itemgetter

import numpy as np
import pytz

from django.conf import settings
from django.db import models, transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.charts.utils import midnight, end_of_day
from tracpro.client import get_client
from tracpro.contacts.models import Contact, NoMatchingCohortsWarning
from tracpro.groups.models import Region

from . import rules
from .tasks import pollrun_start
from .utils import extract_words, natural_sort_key, just_floats


SAMEDAY_LAST = 'use_last'
SAMEDAY_SUM = 'sum'


class PollQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def by_org(self, org):
        return self.filter(org=org)


class PollManager(models.Manager.from_queryset(PollQuerySet)):

    def from_temba(self, org, temba_poll):
        """
        Create new or update existing Poll from RapidPro data.

        :param TembaFlow temba_poll:
        """
        poll, _ = self.get_or_create(org=org, flow_uuid=temba_poll.uuid)

        if poll.name == poll.rapidpro_name:
            # Name is tracking RapidPro name so we must update both.
            poll.name = poll.rapidpro_name = temba_poll.name
        else:
            # Custom name will be maintained despite update of RapidPro name.
            poll.rapidpro_name = temba_poll.name

        poll.save()

        return poll

    @transaction.atomic
    def set_active_for_org(self, org, uuids):
        """Set matching org Polls to be active, and all others to be inactive.

        If an invalid UUID is given, a ValueError is raised and the transaction
        is rolled back.
        """
        active_count = org.polls.filter(flow_uuid__in=uuids).update(is_active=True)
        if active_count != len(uuids):
            invalid_uuids = set(uuids) - set(org.polls.values_list('flow_uuid', flat=True))
            raise ValueError(
                "No Poll for {} matching these UUIDS: {}".format(
                    org.name, invalid_uuids))
        org.polls.exclude(flow_uuid__in=uuids).update(is_active=False)

    def sync(self, org):
        """Update the org's Polls from RapidPro."""
        # Retrieve current Polls known to RapidPro.
        temba_polls_result = get_client(org).get_flows()

        # Filter out polls with names starting with 'Single Message'
        temba_polls = {}
        for poll in temba_polls_result:
            if not poll.name.startswith('Single Message'):
                temba_polls[poll.uuid] = poll

        # Remove Polls that are no longer on RapidPro or that we are filtering out.
        org.polls.exclude(flow_uuid__in=temba_polls.keys()).delete()

        # Create new or update existing Polls to match RapidPro data.
        for temba_poll in temba_polls.values():
            Poll.objects.from_temba(org, temba_poll)


@python_2_unicode_compatible
class Poll(models.Model):
    """Corresponds to a RapidPro flow.

    Keeping track of contact responses to a flow is data-intensive, so Tracpro
    only tracks flows that the user has selected. Selected flows are managed
    as Polls.
    """
    flow_uuid = models.CharField(max_length=36)
    org = models.ForeignKey(
        'orgs.Org', related_name='polls', verbose_name=_('org'))
    rapidpro_name = models.CharField(
        max_length=64, verbose_name=_('RapidPro name'))
    name = models.CharField(
        max_length=64, blank=True, verbose_name=_('name'))

    # Set this to False rather than deleting a Poll. If the user should
    # re-select the corresponding flow later, we can avoid re-importing
    # existing data.
    is_active = models.BooleanField(
        default=False, verbose_name=_("show on TracPro"))

    objects = PollManager()

    class Meta:
        unique_together = (
            ('org', 'flow_uuid'),
        )

    def __init__(self, *args, **kwargs):
        """Name should default to the RapidPro name."""
        super(Poll, self).__init__(*args, **kwargs)
        self.name = self.name or self.rapidpro_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Don't save custom name if it is the same as the RapidPro name.

        This allows us to track changes to the name on RapidPro.
        """
        self.name = "" if self.name == self.rapidpro_name else self.name.strip()
        super(Poll, self).save(*args, **kwargs)
        self.name = self.name or self.rapidpro_name


class QuestionQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)


class QuestionManager(models.Manager.from_queryset(QuestionQuerySet)):

    def from_temba(self, poll, temba_question, order):
        """Create new or update existing Question from RapidPro data."""
        question, _ = self.get_or_create(poll=poll, ruleset_uuid=temba_question['uuid'])

        if question.name == question.rapidpro_name:
            # Name is tracking RapidPro name so we must update both.
            question.name = question.rapidpro_name = temba_question['label']
        else:
            # Custom name will be maintained despite update of RapidPro name.
            question.rapidpro_name = temba_question['label']

        # Save the rules used to categorize answers to this question.
        rules = []
        for rule in temba_question['rules'][:-1]:  # The last rule is always "Other".
            rules.append({
                'category': rule['category'],
                'test': rule['test'],
            })
        question.json_rules = json.dumps(rules)

        # The user can alter or correct the question's type after it is
        # initially set, so we shouldn't override the existing type.
        if not question.question_type:
            question.question_type = question.guess_question_type()

        question.order = order
        question.save()

        return question


@python_2_unicode_compatible
class Question(models.Model):
    """Corresponds to RapidPro RuleSet."""
    TYPE_OPEN = 'O'
    TYPE_MULTIPLE_CHOICE = 'C'
    TYPE_NUMERIC = 'N'
    TYPE_MENU = 'M'
    TYPE_KEYPAD = 'K'
    TYPE_RECORDING = 'R'
    TYPE_CHOICES = (
        (TYPE_OPEN, _("Open Ended")),
        (TYPE_MULTIPLE_CHOICE, _("Multiple Choice")),
        (TYPE_NUMERIC, _("Numeric")),
        (TYPE_MENU, _("Menu")),
        (TYPE_KEYPAD, _("Keypad")),
        (TYPE_RECORDING, _("Recording")),
    )

    ruleset_uuid = models.CharField(max_length=36)
    poll = models.ForeignKey(
        'polls.Poll', related_name='questions', verbose_name=_('poll'))
    rapidpro_name = models.CharField(
        max_length=64, verbose_name=_('RapidPro name'))
    name = models.CharField(
        max_length=64, blank=True, verbose_name=_('name'))
    question_type = models.CharField(
        max_length=1, choices=TYPE_CHOICES, verbose_name=_('question type'))
    order = models.IntegerField(
        default=0, verbose_name=_('order'))
    is_active = models.BooleanField(
        default=True, verbose_name=_("show on TracPro"))
    json_rules = models.TextField(
        blank=True,
        verbose_name=_("RapidPro rules"))

    objects = QuestionManager()

    class Meta:
        ordering = ('order',)
        unique_together = (
            ('ruleset_uuid', 'poll'),
        )

    def __init__(self, *args, **kwargs):
        """Name should default to the RapidPro name."""
        super(Question, self).__init__(*args, **kwargs)
        self.name = self.name or self.rapidpro_name

    def __str__(self):
        return self.name

    def categorize(self, value):
        """Return the first category that the value matches."""
        for rule in self.get_rules():
            if rules.passes_test(value, rule):
                return rules.get_category(rule)
        return "Other"

    def get_rules(self):
        if not hasattr(self, "_rules"):
            self._rules = json.loads(self.json_rules) if self.json_rules else []
        return self._rules

    def guess_question_type(self):
        """Inspect rules applied to question input to guess data type.

        Historically, the "response_type" field on the ruleset was used to
        determine question type. This field appears to have been deprecated
        and currently returns from a limited subset of possible types.
        """
        # Collect the type of each test applied to question input, e.g.,
        # "has any of these words", "has a number", "has a number between", etc.
        tests = [rule['test']['type'] for rule in self.get_rules()]

        if not tests:
            return self.TYPE_OPEN
        elif all(t in rules.NUMERIC_TESTS for t in tests):
            return self.TYPE_NUMERIC
        else:
            return self.TYPE_MULTIPLE_CHOICE

    def save(self, *args, **kwargs):
        """Don't save custom name if it is the same as the RapidPro name.

        This allows us to track changes to the name on RapidPro.
        """
        self.name = "" if self.name == self.rapidpro_name else self.name.strip()
        super(Question, self).save(*args, **kwargs)
        self.name = self.name or self.rapidpro_name


class PollRunQuerySet(models.QuerySet):

    def active(self):
        """Return all active PollRuns."""
        return self.filter(poll__is_active=True)

    def by_dates(self, start_date=None, end_date=None):
        pollruns = self.all()
        if start_date:
            pollruns = pollruns.filter(conducted_on__gte=start_date)
        if end_date:
            pollruns = pollruns.filter(conducted_on__lt=end_date)
        return pollruns

    def by_region(self, region, include_subregions=True):
        """Return all PollRuns for the region."""
        if not region:
            return self.all()

        q = Q(region=region)

        # Include PollRuns that include this region as a sub-region.
        q |= Q(region__in=region.get_ancestors(),
               pollrun_type=PollRun.TYPE_PROPAGATED)

        # Include poll runs that weren't sent to a particular region.
        q |= Q(region=None)

        # Include PollRuns that were sent to the region's sub-regions.
        if include_subregions:
            q |= Q(region__in=region.get_descendants())

        return self.filter(q)

    def by_org(self, org):
        return self.filter(poll__org=org)

    def universal(self):
        types = (PollRun.TYPE_UNIVERSAL, PollRun.TYPE_SPOOFED)
        return self.filter(pollrun_type__in=types)


class PollRunManager(models.Manager.from_queryset(PollRunQuerySet)):

    def create(self, poll, region=None, **kwargs):
        if region and poll.org != region.org:
            raise ValueError("Region org must match poll org.")
        return super(PollRunManager, self).create(poll=poll, region=region, **kwargs)

    def create_regional(self, region, do_start=True, **kwargs):
        """Create a poll run for a single region."""
        if not region:
            raise ValueError("Panel poll requires a non-null panel.")
        kwargs['pollrun_type'] = PollRun.TYPE_REGIONAL
        pollrun = self.create(region=region, **kwargs)
        if do_start:
            pollrun_start.delay(pollrun.pk)
        return pollrun

    def create_propagated(self, region, do_start=True, **kwargs):
        """Create a poll run for a region and its sub-regions."""
        if not region:
            raise ValueError("Propagated poll requires a non-null panel.")
        kwargs['pollrun_type'] = PollRun.TYPE_PROPAGATED
        pollrun = self.create(region=region, **kwargs)
        if do_start:
            pollrun_start.delay(pollrun.pk)
        return pollrun

    def create_spoofed(self, **kwargs):
        kwargs['pollrun_type'] = PollRun.TYPE_SPOOFED
        return self.create(**kwargs)

    def get_or_create_universal(self, poll, for_date=None, **kwargs):
        """Create a poll run that is for all regions."""
        # Get the requested date in the org timezone
        for_date = for_date or timezone.now()
        if isinstance(poll.org.timezone, basestring):
            org_timezone = pytz.timezone(poll.org.timezone)
        else:
            org_timezone = poll.org.timezone
        for_local_date = for_date.astimezone(org_timezone).date()

        # look for a non-regional pollrun on that date
        sql = ('SELECT * FROM polls_pollrun WHERE poll_id = %s AND '
               'region_id IS NULL AND DATE(conducted_on AT TIME ZONE %s) = %s')
        params = [poll.pk, org_timezone.zone, for_local_date]
        existing = list(PollRun.objects.raw(sql, params))
        if existing:
            return existing[0]

        kwargs['poll'] = poll
        kwargs['region'] = None
        kwargs['pollrun_type'] = PollRun.TYPE_UNIVERSAL
        kwargs['conducted_on'] = for_date
        return self.create(**kwargs)

    def get_all(self, org, region, include_subregions=True):
        """
        Get all active PollRuns for the region, plus sub-regions if
        specified.
        """
        qs = self.get_queryset().active().by_org(org)
        qs = qs.select_related('poll', 'region')
        qs = qs.by_region(region, include_subregions)
        return qs


@python_2_unicode_compatible
class PollRun(models.Model):
    """Associates polls conducted on the same day."""

    TYPE_UNIVERSAL = 'u'  # Sent to all active regions.
    TYPE_SPOOFED = 's'  # Universal PollRun created by baseline data spoof.
    TYPE_REGIONAL = 'r'  # Sent to only one region.
    TYPE_PROPAGATED = 'p'  # Sent to one region and its sub-regions.
    TYPE_CHOICES = (
        (TYPE_UNIVERSAL, _('Universal')),
        (TYPE_SPOOFED, _('Spoofed')),
        (TYPE_REGIONAL, _('Single Panel')),
        (TYPE_PROPAGATED, _('Propagated to sub-children')),
    )

    pollrun_type = models.CharField(
        max_length=1, editable=False, choices=TYPE_CHOICES)

    poll = models.ForeignKey('polls.Poll', related_name='pollruns')

    region = models.ForeignKey(
        'groups.Region', blank=True, null=True,
        verbose_name=_('panel'),
        help_text=_("Panel where the poll was conducted."))

    conducted_on = models.DateTimeField(
        help_text=_("When the poll was conducted"), default=timezone.now)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name="pollruns_created")

    objects = PollRunManager()

    def __str__(self):
        return "{poll} ({when})".format(
            poll=self.poll.name,
            when=self.conducted_on.strftime(settings.SITE_DATE_FORMAT),
        )

    def as_json(self, region=None, include_subregions=True):
        return {
            'id': self.pk,
            'poll': {
                'id': self.poll.pk,
                'name': self.poll.name,
            },
            'conducted_on': self.conducted_on,
            'region': {'id': self.region.pk, 'name': self.region.name} if self.region else None,
            'responses': self.get_response_counts(region, include_subregions),
        }

    def covers_region(self, region, include_subregions):
        """Return whether this PollRun is related to all given regions."""
        if not region or region.pk == self.region_id:
            # Shortcut to minimize more expensive queries later.
            return True

        if self.pollrun_type in (self.TYPE_UNIVERSAL, self.TYPE_SPOOFED):
            return True
        if self.pollrun_type == self.TYPE_REGIONAL:
            if include_subregions:
                return region in self.region.get_ancestors()
            else:  # pragma: nocover
                return region == self.region
        if self.pollrun_type == self.TYPE_PROPAGATED:
            if include_subregions:
                return region in self.region.get_family()
            else:
                return region in self.region.get_descendants()

    def get_responses(self, region=None, include_subregions=True,
                      include_empty=True):
        """Return queryset of all PollRun responses for this region and sub-regions."""
        if not self.covers_region(region, include_subregions):
            raise ValueError(
                "Request for responses in panel where poll wasn't conducted")
        responses = self.responses.filter(
            is_active=True,
            contact__region__is_active=True,
            contact__is_active=True)  # Filter out inactive contacts
        if region:
            if include_subregions:
                regions = region.get_descendants(include_self=True)
                responses = responses.filter(contact__region__in=regions)
            else:
                responses = responses.filter(contact__region=region)
        if not include_empty:
            responses = responses.exclude(status=Response.STATUS_EMPTY)
        return responses.select_related('contact')

    def get_response_counts(self, region=None, include_subregions=True):
        """
        Returns dictionary of PollRun response counts for this region and sub-regions.
        key = str 'status' field from response
        value = int count of responses with that status.
        """
        status_counts = self.get_responses(region, include_subregions)
        status_counts = status_counts.values('status')
        status_counts = status_counts.annotate(count=Count('status'))
        results = {status[0]: 0 for status in Response.STATUS_CHOICES}
        results.update({sc['status']: sc['count'] for sc in status_counts})
        return results

    def is_last_for_region(self, region):
        """Return whether this was the last PollRun conducted in the region.

        Includes universal PollRuns.
        """
        if not self.covers_region(region, include_subregions=False):
            return False
        newer_pollruns = PollRun.objects.filter(
            poll=self.poll,
            conducted_on__gt=self.conducted_on,
        ).by_region(region, include_subregions=False)
        return not newer_pollruns.exists()


class ResponseQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def group_counts(self, *fields):
        """Group responses by the given fields then map to the count of matching responses."""
        responses = self.order_by(*fields).values(*fields)
        data = {}
        for field_values, _responses in groupby(responses, itemgetter(*fields)):
            data[field_values] = len(list(_responses))
        return data


class Response(models.Model):
    """Corresponds to RapidPro FlowRun."""
    STATUS_EMPTY = 'E'
    STATUS_PARTIAL = 'P'
    STATUS_COMPLETE = 'C'
    STATUS_CHOICES = (
        (STATUS_EMPTY, _("Empty")),
        (STATUS_PARTIAL, _("Partial")),
        (STATUS_COMPLETE, _("Complete")),
    )

    flow_run_id = models.IntegerField(null=True)

    pollrun = models.ForeignKey('polls.PollRun', null=True, related_name='responses')

    contact = models.ForeignKey('contacts.Contact', related_name='responses')

    created_on = models.DateTimeField(
        help_text=_("When this response was created"))

    updated_on = models.DateTimeField(
        help_text=_("When the last activity on this response was"))

    status = models.CharField(
        max_length=1, verbose_name=_("Status"), choices=STATUS_CHOICES,
        help_text=_("Current status of this response"))

    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this response is active"))

    objects = ResponseQuerySet.as_manager()

    class Meta:
        unique_together = [
            ('flow_run_id', 'pollrun'),
        ]

    @classmethod
    def create_empty(cls, org, pollrun, run):
        """
        Creates an empty response from a run. Used to start or restart a
        contact in an existing pollrun.
        """
        contact = Contact.get_or_fetch(org, uuid=run.contact)

        # de-activate any existing responses for this contact
        pollrun.responses.filter(contact=contact).update(is_active=False)

        return Response.objects.create(
            flow_run_id=run.id, pollrun=pollrun, contact=contact,
            created_on=run.created_on, updated_on=run.created_on,
            status=Response.STATUS_EMPTY)

    @classmethod
    def from_run(cls, org, run, poll=None):
        """
        Gets or creates a response from a flow run and returns the response.

        If response is not up-to-date with provided run, then it is updated.

        If the run doesn't match with an existing poll pollrun, it's assumed
        to be non-regional.

        If a new response has been created, the returned response will have
        attribute `is_new` = True.

        :param run: temba Run instance
        :param poll: tracpro Poll instance, or None
        """
        responses = Response.objects.filter(pollrun__poll__org=org, flow_run_id=run.id)
        response = responses.select_related('pollrun').first()
        run_updated_on = cls.get_run_updated_on(run)

        # if there is an up-to-date existing response for this run, return it
        if response and response.updated_on == run_updated_on:
            return response

        if not poll:
            poll = Poll.objects.active().by_org(org).get(flow_uuid=run.flow.uuid)

        try:
            contact = Contact.get_or_fetch(poll.org, uuid=run.contact.uuid)
        except NoMatchingCohortsWarning:
            # Callers expect a ValueError if we don't sync the response
            raise ValueError(
                "not syncing run because contact %s does not exist locally and has no matching cohorts among %r"
                % (run.contact.uuid, Region.get_all(org)))

        # categorize completeness
        if run.exit_type == u'completed':
            status = Response.STATUS_COMPLETE
        elif run.values:
            status = Response.STATUS_PARTIAL
        else:
            status = Response.STATUS_EMPTY

        if response:
            # clear existing answers which will be replaced
            response.answers.all().delete()

            response.updated_on = run_updated_on
            response.status = status
            response.save(update_fields=('updated_on', 'status'))
        else:
            # if we don't have an existing response, then this poll started in
            # RapidPro and is non-regional
            pollrun = PollRun.objects.get_or_create_universal(
                poll=poll,
                for_date=run.created_on,
            )

            response = Response.objects.create(
                is_active=True,  # default, just being explicit
                flow_run_id=run.id, pollrun=pollrun, contact=contact,
                created_on=run.created_on, updated_on=run_updated_on,
                status=status)

            # If more than one for this contact and pollrun,
            # set the last one created as the active one.
            if Response.objects.filter(pollrun=pollrun, contact=contact).count() > 1:
                # Set them all False, then the one we want true
                with transaction.atomic():
                    Response.objects.filter(pollrun=pollrun, contact=contact).update(is_active=False)
                    last = Response.objects.filter(pollrun=pollrun, contact=contact).order_by('-created_on').first()
                    last.is_active = True
                    last.save()

            response.is_new = True

        # organize values by ruleset UUID
        questions = poll.questions.active()
        valuesets_by_ruleset = {value.node: value for key, value in run.values.iteritems()}
        valuesets_by_question = {q: valuesets_by_ruleset.get(q.ruleset_uuid, None)
                                 for q in questions}

        # convert valuesets to answers
        for question, valueset in valuesets_by_question.iteritems():
            if valueset:
                Answer.objects.create(
                    response=response,
                    question=question,
                    value=valueset.value,
                    category=valueset.category,
                    submitted_on=valueset.time,
                )

        return response

    @classmethod
    def get_run_updated_on(cls, run):
        # find the result with the latest time
        last_value_on = None

        for key, value in run.values.iteritems():
            if not last_value_on or value.time > last_value_on:
                last_value_on = value.time

        return last_value_on if last_value_on else run.created_on


class AnswerQuerySet(models.QuerySet):

    def word_counts(self):
        answers = self.values_list('value_to_use', 'response__contact__language')
        words = [extract_words(*a) for a in answers]
        counts = Counter(chain(*words))
        return counts.most_common(50)

    def group_values(self, *fields):
        """Group answers by the given fields then map to a list of matching values."""
        answers = self.order_by(*fields).values('value_to_use', *fields)
        data = {}
        for field_values, _answers in groupby(answers, itemgetter(*fields)):
            data[field_values] = [a['value_to_use'] for a in _answers]
        return data

    def category_counts(self):
        categories = self.values_list('category', flat=True)
        counts = Counter(categories)
        return counts.most_common()

    def autocategorize(self):
        """
        Break down numeric answers into categories automatically, based somewhat
        on ranges where there are bunches of responses.

        See http://numpy.readthedocs.io/en/stable/reference/generated/numpy.histogram.html
        where we're using the 'sqrt' bin assignment algorithm.

        Silently ignores answers where `category` != "numeric", and any whose value
        can't be successfully converted to a float.

        Returns dictionary {
          'categories': list of category names in order,
          'data': list of counts in order
        }

        Category names are of the form "N.N-N.N".
        """
        answers_to_numeric_questions = self.filter(question__question_type=Question.TYPE_NUMERIC)
        answers = just_floats(answers_to_numeric_questions.values_list('value_to_use', flat=True))
        if not answers:
            return {
                'categories': [],
                'data': [],
            }

        hist, bin_edges = np.histogram(answers, bins='sqrt')
        category_names = [
            "%r-%r" % (round(bin_edges[i], 2), round(bin_edges[i+1], 2))
            for i in range(len(hist))
        ]
        data = list(hist)

        return {
            'categories': category_names,
            'data': data,
        }

    def category_counts_by_pollrun(self):
        """
        Returns list of (categoryname, Counter) tuples, sorted by category name.
        Each Counter breaks down the number of answers per poll run.
        """
        counts = []
        answers = self.order_by('category').values('category', 'response__pollrun')
        for category, _answers in groupby(answers, itemgetter('category')):
            pollrun_counts = Counter(a['response__pollrun'] for a in _answers)
            counts.append((category, pollrun_counts))

        # Order the data by the category name.
        counts.sort(key=lambda (category, pollrun_counts): natural_sort_key(category))
        return counts


class AnswerManager(models.Manager.from_queryset(AnswerQuerySet)):

    def create(self, category, **kwargs):
        # category can be a string or a multi-language dict
        if isinstance(category, dict):
            if 'base' in category:
                category = category['base']
            else:
                category = category.itervalues().next()

        if category == 'All Responses':
            category = None

        return super(AnswerManager, self).create(category=category, **kwargs)


class Answer(models.Model):
    """
    Corresponds to RapidPro FlowStep.
    In Temba API, corresponds to one entry in the Run.Value dictionary.
    """

    response = models.ForeignKey('polls.Response', related_name='answers')
    question = models.ForeignKey('polls.Question', related_name='answers')
    value = models.CharField(
        max_length=640, null=True,
        help_text="Value from rapidpro")
    value_to_use = models.CharField(
        max_length=640, null=True,
        help_text=_("For numeric questions for orgs that want to use the sum of numeric "
                    "responses from the same contact on the same day, the sum of those "
                    "responses. For all others, just a copy of 'value'.")
    )

    category = models.CharField(max_length=36, null=True)
    submitted_on = models.DateTimeField(
        help_text=_("When this answer was submitted"))

    objects = AnswerManager()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.should_use_sum():
            self.value_to_use = self.value
        super(Answer, self).save(*args, **kwargs)
        if is_new and self.should_use_sum():
            # We created a new answer - we need to update the summed
            # values in this and maybe other answers
            self.update_own_summed_values_and_others()

    def update_own_summed_values_and_others(self):
        """
        Update the summed value for this answer, and any others on
        the same day/contact/question.
        """
        answers = self.same_question_contact_and_day()
        value = self.compute_value_to_use()
        # Update the database
        answers.update(value_to_use=value)
        # And update this particular record in memory to avoid confusion
        self.value_to_use = value

    def should_use_sum(self):
        """
        Return true if we should use a sum of response values from
        the same contact on the same day for the same question
        for this answer.
        """
        question = self.question
        org = question.poll.org
        return (org.how_to_handle_sameday_responses == SAMEDAY_SUM and
                question.question_type == Question.TYPE_NUMERIC)

    def same_question_contact_and_day(self):
        """
        Return a queryset of answers that are the same question,
        contact, and day as this one (includes this one).
        """
        return Answer.objects.filter(
            question_id=self.question_id,
            response__contact_id=self.response.contact_id,
            submitted_on__gte=midnight(self.submitted_on),
            submitted_on__lte=end_of_day(self.submitted_on),
        )

    def compute_value_to_use(self):
        """
        Normally, just return the value from rapidpro.
        But if it's a numeric question and
        the org is configured to sum multiple responses on the same day from
        the same contact, look up all the answers from that contact to this
        question on this same day and return the sum of them as a float.
        """
        assert self.pk  # Don't use on unsaved records, it'll miss this record's value
        if self.should_use_sum():
            # Include inactive responses from same contact on same day and
            # add them all up, including this one
            values = [float(a.value) for a in self.same_question_contact_and_day()]
            return "%f" % sum(values)
        else:
            return self.value
