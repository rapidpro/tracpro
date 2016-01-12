from django.core.urlresolvers import reverse
from django.utils import timezone

from temba_client.types import Run

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import PollRun, Question, Response
from .. import charts


class PollChartTest(TracProDataTest):

    def setUp(self):
        super(PollChartTest, self).setUp()

        self.poll1_question1.question_type = Question.TYPE_MULTIPLE_CHOICE
        self.poll1_question1.save()

        self.poll1_question2.question_type = Question.TYPE_OPEN
        self.poll1_question2.save()

        self.pollrun = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())
        self.pollruns = PollRun.objects.filter(pk=self.pollrun.pk)

        response1 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=123, contact=self.contact1.uuid, created_on=timezone.now()))
        factories.Answer(
            response=response1, question=self.poll1_question1,
            value="4.00000", category="1 - 5")
        factories.Answer(
            response=response1, question=self.poll1_question2,
            value="It's very rainy", category="All Responses")

        response2 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=234, contact=self.contact2.uuid, created_on=timezone.now()))
        factories.Answer(
            response=response2, question=self.poll1_question1,
            value="3.00000", category="1 - 5")
        factories.Answer(
            response=response2, question=self.poll1_question2,
            value="rainy and rainy", category="All Responses")

        response3 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=345, contact=self.contact4.uuid, created_on=timezone.now()))
        factories.Answer(
            response=response3, question=self.poll1_question1,
            value="8.00000", category="6 - 10")
        factories.Answer(
            response=response3, question=self.poll1_question2,
            value="Sunny sunny", category="All Responses")

        # Set all responses to COMPLETE so that they can be found in charting functions
        Response.objects.all().update(status=Response.STATUS_COMPLETE)

        self.regions = []

    def test_multiple_pollruns_multiple_choice(self):
        question = self.poll1_question1
        data = charts.multiple_pollruns_multiple_choice(
            self.pollruns, question, self.regions)

        self.assertEqual(
            data['dates'],
            [self.pollrun.conducted_on.strftime('%Y-%m-%d')])
        self.assertEqual(data['series'], [
            {'name': u'1 - 5',
             'data': [{u'y': 2, u'url': u'/pollrun/read/1/'}]},
            {'name': u'6 - 10',
             'data': [{u'y': 1, u'url': u'/pollrun/read/1/'}]},
            {'name': None,
             'data': [{u'y': 3, u'url': u'/pollrun/read/1/'}]},
        ])

    def test_multiple_pollruns_open(self):
        question = self.poll1_question2
        data = charts.multiple_pollruns_open(
            self.pollruns, question, self.regions)
        self.assertEqual(data, [
            {"text": "rainy", "weight": 3},
            {"text": "sunny", "weight": 2},
        ])

    def test_multiple_pollruns_numeric(self):
        # Reset question 1 type to NUMERIC
        # Answers are 4, 3 and 8 for a single date (today)

        self.poll1_question1.question_type = Question.TYPE_NUMERIC
        self.poll1_question1.save()
        data = charts.multiple_pollruns_numeric(
            self.pollruns, self.poll1_question1, self.regions)

        # Single item for single date: sum = 4 + 3 + 8 = 15
        # URL points to pollrun detail page for this date
        self.assertEqual(
            data['sum'],
            [{"y": 15.0, "url": reverse('polls.pollrun_read', args=[self.pollrun.pk])}])

        # Single item for single date: average = (4 + 3 + 8)/3 = 5
        # URL points to pollrun detail page for this date
        self.assertEqual(
            data['average'],
            [{"y": 5.0, "url": reverse('polls.pollrun_read', args=[self.pollrun.pk])}])

        # Set all responses to complete in setUp()
        # Response rate = 100%
        # URL points to participation tab
        self.assertEqual(
            data['response-rate'],
            [{"y": 100.0, "url": reverse('polls.pollrun_participation', args=[self.pollrun.pk])}])

        # Today's date
        self.assertEqual(
            data['dates'],
            [self.pollrun.conducted_on.strftime('%Y-%m-%d')])

        # Mean, Standard Dev, response rate avg, pollrun list
        self.assertEqual(
            self.poll1_question1.answer_mean,
            5.0)
        self.assertEqual(
            self.poll1_question1.answer_stdev,
            0.0)
        self.assertEqual(
            self.poll1_question1.response_rate_average,
            100.0)

        # Set one of the responses to partial, changing the response rate
        Response.objects.filter(contact=self.contact1).update(status=Response.STATUS_PARTIAL)

        data = charts.multiple_pollruns_numeric(
            self.pollruns, self.poll1_question1, self.regions)

        # 2 complete responses, 1 partial response
        # Response rate = 66.67%
        self.assertEqual(
            data['response-rate'],
            [{"y": 66.67, "url": reverse('polls.pollrun_participation', args=[self.pollrun.pk])}])
        self.assertEqual(
            self.poll1_question1.response_rate_average,
            66.67)
