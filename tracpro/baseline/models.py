from django.db import models
from django.utils.translation import ugettext_lazy as _

from smart_selects.db_fields import ChainedForeignKey

from tracpro.polls.models import Answer, Question, Poll


class BaselineTerm(models.Model):
    """
    e.g., 2015 Term 3 Attendance for P3 Girls
     A term of time to gather statistics for a baseline chart
     baseline_question: the answer to this will determine our baseline
                        information for all dates
                        ie. How many students are enrolled?
     follow_up_question: the answers to this question will determine the
                         follow-up information, over the date range
                         (start_date -> end_date)
                         ie. How many students attended today?
    """

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
        help_text=_("The least recent response per user will be used as the baseline.")
    )

    follow_up_poll = models.ForeignKey(Poll)
    follow_up_question = ChainedForeignKey(
        Question,
        chained_field='follow_up_poll',
        chained_model_field='poll',
        auto_choose=True,
        help_text=_("Responses over time to compare to the baseline.")
    )
    y_axis_title = models.CharField(max_length=255, null=True, blank=True,
                                    help_text=_("The title for the y axis of the chart."))

    @classmethod
    def get_all(cls, org):
        baseline_terms = cls.objects.filter(org=org)
        return baseline_terms

    def get_baseline(self, region):
        """ Get all baseline responses """
        baseline_answers = Answer.objects.filter(
            question=self.baseline_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        ).select_related('response')

        if region:
            baseline_answers = baseline_answers.filter(response__contact__region=region)

        region_answers = {}
        regions = baseline_answers.values('response__contact__region__name').distinct(
            'response__contact__region__name').order_by('response__contact__region__name')
        dates = []
        # Separate out baseline values per region
        for region in regions:
            region_name = region['response__contact__region__name'].encode('ascii')
            answers_by_region = baseline_answers.filter(response__contact__region__name=region_name)
            answer_sums, dates = answers_by_region.numeric_sum_group_by_date()

            region_answers[region_name] = {}
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
        """
        Loop through all regions in answers and create
        a dict of values and dates per Region
        ex.
        { 'Kumpala': {'values': [35,...], 'dates': [datetime.date(2015, 8, 12),...]} }
        """
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
