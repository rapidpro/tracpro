from collections import defaultdict

from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from smart_selects.db_fields import ChainedForeignKey

from tracpro.polls.models import Answer, Question, Poll


class BaselineTerm(models.Model):
    # e.g., 2015 Term 3 Attendance for P3 Girls
    # A term of time to gather statistics for a baseline chart
    # baseline_question: the answer to this will determine our baseline
    #                    information for all dates
    #                    ie. How many students are enrolled?
    # follow_up_question: the answers to this question will determine the
    #                     follow-up information, over the date range
    #                     (start_date -> end_date)
    #                     ie. How many students attended today?

    org = models.ForeignKey("orgs.Org", verbose_name=_(
        "Organization"), related_name="baseline_terms")
    name = models.CharField(max_length=255, help_text=_(
        "For example: 2015 Term 3 Attendance for P3 Girls"))
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    baseline_poll = models.ForeignKey(Poll, related_name="baseline_terms")
    baseline_question = ChainedForeignKey(
        Question,
        chained_field='baseline_poll',
        chained_model_field='poll',
        auto_choose=True,
        related_name="baseline_terms",
        help_text=_("All baseline poll results over time will display in chart.")
    )

    follow_up_poll = models.ForeignKey(Poll)
    follow_up_question = ChainedForeignKey(
        Question,
        chained_field='follow_up_poll',
        chained_model_field='poll',
        auto_choose=True,
        help_text=_("Follow up poll responses over time to compare to the baseline values.")
    )
    y_axis_title = models.CharField(max_length=255, null=True, blank=True,
                                    help_text=_("The title for the y axis of the chart."))

    @classmethod
    def get_all(cls, org):
        baseline_terms = cls.objects.filter(org=org)
        return baseline_terms

    def get_baseline(self, regions):
        """ Get all baseline responses """
        answers = Answer.objects.filter(
            question=self.baseline_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # TODO: look into timezone
        )
        answers = answers.annotate(region_name=F('response__contact__region__name'))
        answers = answers.select_related('response', 'response__contact')

        # Results should be limited to the requested region(s).
        if regions:
            answers = answers.filter(response__contact__region__in=regions)

        # Separate out baseline values per region
        region_answers = defaultdict(dict)
        dates = []
        for region_name in set(a.region_name.encode('ascii') for a in answers):
            answers_by_region = answers.filter(region_name=region_name)
            answer_sums, dates = answers_by_region.numeric_sum_group_by_date()
            region_answers[region_name]["values"] = answer_sums
        return region_answers, dates

    def get_follow_up(self, region):
        """ Get all follow up responses summed by region """
        answers = Answer.objects.filter(
            question=self.follow_up_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        ).select_related('response')
        if region:
            answers = answers.filter(response__contact__region=region)
        # Loop through all regions in answers and create
        # a dict of values and dates per Region
        # ex.
        # { 'Kumpala': {'values': [35,...], 'dates': [datetime.date(2015, 8, 12),...]} }
        region_answers = {}
        dates = []
        regions = answers.values('response__contact__region__name').distinct(
            'response__contact__region__name').order_by('response__contact__region__name')
        for region in regions:
            region_name = region['response__contact__region__name'].encode('ascii')
            answers_by_region = answers.filter(response__contact__region__name=region_name)
            answer_sums, dates = answers_by_region.numeric_sum_group_by_date()
            region_answers[region_name] = {}
            region_answers[region_name]["values"] = answer_sums

        return region_answers, dates
