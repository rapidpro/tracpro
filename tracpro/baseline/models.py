from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum

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
    def get_all(cls, org):
        baseline_terms = cls.objects.filter(org=org)
        return baseline_terms

    def get_baseline(self, region):
        answers = Answer.objects.filter(
            question=self.baseline_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        ).select_related('response')
        if region:
            answers = answers.filter(response__contact__region=region)
        # Retrieve the most recent baseline results per contact
        baseline_answers = answers.order_by('response__contact', '-submitted_on').distinct('response__contact')

        return list(baseline_answers.values_list("submitted_on", "value", "response__contact__name"))

    def get_follow_up(self, region):
        """ Get all follow up responses """
        # TODO: extra() may be depricated in future versions of Django
        # Look into date_trunc/django
        answers = Answer.objects.filter(
            question=self.follow_up_question,
            submitted_on__gte=self.start_date,
            submitted_on__lte=self.end_date,  # look into timezone
        ).select_related('response').extra({"submitted_on_date": "date(submitted_on)"})
        if region:
            answers = answers.filter(response__contact__region=region)

        answers = answers.order_by("response__contact__name", "submitted_on")

        """
        Loop through all contacts in answers and create
        a dict of values and dates per contact
        ex.
        { 'Erin': {'values': [35,...], 'dates': [datetime.date(2015, 8, 12),...]} }
        """
        # TODO - switch this to sum of all answers by region
        region_answers = {}
        for region in answers.values('response__contact__region__name').distinct('response__contact__region__name').order_by('response__contact__region__name'):
            import ipdb; ipdb.set_trace();
            # TODO: look into Answer.numeric_average()
            region_name = region['response__contact__region__name'].encode('ascii')
            region_answers[region_name] = {}
            region_answers[region_name]["values"] = answers.filter(
                                                      response__contact__region__name=region_name).values_list(
                                                      "value", flat=True)
            region_answers[region_name]["dates"] = answers.filter(
                                                     response__contact__region__name=region_name).values_list(
                                                     "submitted_on_date", flat=True)

        dates = answers.values_list("submitted_on_date").order_by("submitted_on_date").distinct()

        return region_answers, dates
