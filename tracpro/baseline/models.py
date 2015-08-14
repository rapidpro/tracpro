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
                         follow-up information, over the date range (start_date -> end_date)
                         ie. How many students attended today?
    """

    org = models.ForeignKey("orgs.Org", verbose_name=_(
        "Organization"), related_name="baseline_terms")
    region = models.ForeignKey("groups.Region", related_name="baseline_terms")
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
        help_text=_("The most recent response per user will be used as the baseline.")
    )

    follow_up_poll = models.ForeignKey(Poll)
    follow_up_question = ChainedForeignKey(
        Question,
        chained_field='follow_up_poll',
        chained_model_field='poll',
        auto_choose=True,
        help_text=_("Responses over time to compare to the baseline.")
    )

    @classmethod
    def get_all(cls, org, regions=None):
        baseline_terms = cls.objects.filter(org=org)
        if regions:
            baseline_terms = baseline_terms.filter(region__in=regions)
        return baseline_terms

    def get_baseline(self, region):
        answers = Answer.objects.filter(
            response__contact__region=region,
            question=self.baseline_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        )
        answers = answers.order_by("submitted_on")
        baseline_answer = answers.last()
        return baseline_answer.value

    def get_follow_up(self, region):
        answers = Answer.objects.filter(
            response__contact__region=region,
            question=self.follow_up_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        )
        answers = answers.order_by("submitted_on")
        return list(answers.values_list("submitted_on", "value"))
