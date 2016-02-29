from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from smart_selects.db_fields import ChainedForeignKey

from tracpro.groups.models import Region
from tracpro.polls.models import Poll, PollRun, Question, Response


class BaselineTermQuerySet(models.QuerySet):

    def by_org(self, org):
        return self.filter(org=org)


@python_2_unicode_compatible
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

    follow_up_poll = models.ForeignKey(
        Poll, verbose_name=_("Follow Up Poll"), related_name="+")
    follow_up_question = ChainedForeignKey(
        Question, verbose_name=_("Follow Up Question"), related_name="+",
        auto_choose=True,
        chained_field='follow_up_poll', chained_model_field='poll',
        help_text=_("Follow up poll responses over time to compare to the "
                    "baseline values.")
    )

    y_axis_title = models.CharField(
        max_length=255, blank=True, default="",
        help_text=_("The title for the y axis of the chart."))

    objects = BaselineTermQuerySet.as_manager()

    class Meta:
        verbose_name = _("Indicator")

    def __str__(self):
        return self.name

    def _get_indicator_data(self, question, start_date=None, end_date=None,
                            region=None, include_subregions=True,
                            contacts=None):
        if question not in (self.baseline_question, self.follow_up_question):
            raise ValueError("Must be called with the baseline or follow-up "
                             "question.")

        pollruns = PollRun.objects.filter(poll=question.poll_id)
        pollruns = pollruns.order_by('conducted_on')
        pollruns = pollruns.by_dates(
            self.start_date if start_date is None else start_date,
            self.end_date if end_date is None else end_date,
        )
        if region:
            pollruns = pollruns.by_region(region, include_subregions)
        else:
            pollruns = pollruns.universal()

        responses = Response.objects.filter(pollrun__in=pollruns, contact__is_active=True)
        if contacts is not None:
            responses = responses.filter(contact__in=contacts)

        answers = question.answers.filter(response__in=responses)

        return pollruns, responses, answers

    def get_baseline_data(self, **kwargs):
        return self._get_indicator_data(self.baseline_question, **kwargs)

    def get_follow_up_data(self, **kwargs):
        return self._get_indicator_data(self.follow_up_question, **kwargs)

    def get_regions(self):
        """Return regions for the contacts who responded to related polls."""
        questions = [self.baseline_question_id, self.follow_up_question_id]
        regions = Region.objects.filter(
            contacts__responses__answers__question__in=questions)
        regions = regions.distinct().order_by('name')
        return regions
