import datetime

import pytz

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
    start_date = models.DateField()
    end_date = models.DateField()

    baseline_poll = models.ForeignKey(Poll, related_name="+")
    baseline_question = ChainedForeignKey(
        Question, auto_choose=True, related_name="+",
        chained_field='baseline_poll', chained_model_field='poll',
        help_text=_("All baseline poll results over time will display in chart.")
    )

    follow_up_poll = models.ForeignKey(Poll, related_name="+")
    follow_up_question = ChainedForeignKey(
        Question, auto_choose=True, related_name="+",
        chained_field='follow_up_poll', chained_model_field='poll',
        help_text=_("Follow up poll responses over time to compare to the "
                    "baseline values.")
    )

    y_axis_title = models.CharField(max_length=255, null=True, blank=True,
                                    help_text=_("The title for the y axis of the chart."))

    @classmethod
    def get_all(cls, org):
        baseline_terms = cls.objects.filter(org=org)
        return baseline_terms

    def _get_answers(self, question, regions, region_selected):
        """
        Retrieve answers to the question that are relevant for this
        BaselineTerm.
        """
        midnight = datetime.time(0, 0, 0, tzinfo=pytz.utc)
        start = datetime.datetime.combine(self.start_date, midnight)
        end = datetime.datetime.combine(self.end_date + datetime.timedelta(days=1), midnight)

        answers = Answer.objects.filter(
            question=question, submitted_on__gte=start, submitted_on__lt=end)
        answers = answers.annotate(region_name=F('response__contact__region__name'))
        answers = answers.select_related('response', 'response__contact')

        all_regions = answers.values('response__contact__region',
                                     'region_name').distinct('response__contact__region')

        if regions:
            answers = answers.filter(response__contact__region__in=regions)
            all_regions = answers.values('response__contact__region',
                                         'region_name').distinct('response__contact__region')

        if region_selected:
            answers = answers.filter(response__contact__region=region_selected)

        return answers, all_regions

    def get_baseline(self, regions, region_selected):
        """ Get all baseline responses """
        answers, all_regions = self._get_answers(self.baseline_question, regions, region_selected)
        # Separate out baseline values per region
        region_answers = {}
        dates_dict = {}
        for region_name in set(a.region_name.encode('ascii') for a in answers):
            # Retrieve the first result per contact for baseline
            answers_by_region = answers.order_by('response__contact', 'submitted_on').distinct('response__contact')
            answers_by_region = answers_by_region.filter(region_name=region_name)
            answer_sum = answers_by_region.numeric_sum_all_dates()
            region_answers[region_name] = {'values': [answer_sum]}
            dates_dict[region_name] = [self.start_date]
        return region_answers, dates_dict

    def get_follow_up(self, regions, region_selected):
        """ Get all follow up responses summed by region """
        answers, all_regions = self._get_answers(self.follow_up_question, regions, region_selected)

        # Loop through all regions in answers and create
        # a dict of values and dates per Region
        # ex.
        # { 'Kumpala': {'values': [35,...], 'dates': [datetime.date(2015, 8, 12),...]} }
        region_answers = {}
        dates_dict = {}
        dates = []
        for region_name in set(a.region_name.encode('ascii') for a in answers):
            answers_by_region = answers.filter(region_name=region_name)
            answers_by_region = answers_by_region.order_by('submitted_on')
            answer_sums, dates = answers_by_region.numeric_sum_group_by_date()
            region_answers[region_name] = {'values': answer_sums}
            dates_dict[region_name] = dates
        return region_answers, dates_dict, all_regions

    def check_for_data(self, regions):
        answers, all_regions = self._get_answers(self.baseline_question, regions, 0)
        return bool(answers)
