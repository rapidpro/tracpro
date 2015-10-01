import datetime

import pytz

from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from smart_selects.db_fields import ChainedForeignKey

from tracpro.groups.models import Region
from tracpro.polls.models import Answer, Question, Poll, Response


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

    y_axis_title = models.CharField(
        max_length=255, blank=True, default="",
        help_text=_("The title for the y axis of the chart."))

    @classmethod
    def get_all(cls, org):
        baseline_terms = cls.objects.filter(org=org)
        return baseline_terms

    def _get_answers(self, question, regions, region_selected=None):
        """
        Retrieve answers to the question that are relevant for this
        BaselineTerm.
        """
        midnight = datetime.time(0, 0, 0, tzinfo=pytz.utc)
        start = datetime.datetime.combine(self.start_date, midnight)
        end = datetime.datetime.combine(self.end_date + datetime.timedelta(days=1), midnight)

        region_filter = Region.objects.all()
        if regions:
            region_filter = regions
        if region_selected:
            region_filter = Region.objects.filter(pk=region_selected)

        responses = Response.objects.filter(
            contact__region__in=region_filter,
            pollrun__poll=poll,
            pollrun__conducted_on__gte=start,
            pollrun__conducted_on__lt=end)

        import ipdb; ipdb.set_trace()
        answers = Answer.objects.filter(response__in=responses, question=question)
        answers = answers.annotate(region_name=F('response__contact__region__name'))
        answers = answers.select_related('response', 'response__contact')

        import ipdb; ipdb.set_trace()
        if regions:
            all_regions = regions
        else:
            # TODO: get all regions for the drop down here... not sure how to do this yet!
            all_regions = Region.objects.all()

        return answers, all_regions

    def get_baseline(self, regions, region_selected=None):
        """ Get all baseline responses """
        answers, all_regions = self._get_answers(self.baseline_question, self.baseline_poll, regions, region_selected)
        # Retrieve the first result per contact for baseline
        answers = answers.order_by('response__contact', 'submitted_on').distinct('response__contact')
        answer_sum = answers.numeric_sum_all_dates()
        dates_list = [self.start_date]
        return answer_sum, dates_list

    def get_follow_up(self, regions, region_selected=None):
        """ Get all follow up responses """
        answers, all_regions = self._get_answers(self.follow_up_question, self.follow_up_poll, regions, region_selected)

        answers = answers.order_by('submitted_on')
        answers_list, dates = answers.numeric_sum_group_by_date()
        return answers_list, dates, all_regions

    def check_for_data(self, regions):
        answers, all_regions = self._get_answers(self.baseline_question, regions, 0)
        return answers.exists()
