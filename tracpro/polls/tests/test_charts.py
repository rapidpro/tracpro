from collections import OrderedDict

from django.utils import timezone

from temba_client.types import Run

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import PollRun, Question, Response
from ..charts import multiple_pollruns_non_numeric


class PollChartTest(TracProDataTest):

    def setUp(self):
        super(PollChartTest, self).setUp()

        self.poll1_question1.question_type = Question.TYPE_MULTIPLE_CHOICE
        self.poll1_question1.save()

        self.poll1_question2.question_type = Question.TYPE_OPEN
        self.poll1_question2.save()

        self.pollrun = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())

        response1 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=123, contact='C-001', created_on=timezone.now()))
        factories.Answer(
            response=response1, question=self.poll1_question1,
            value="4.00000", category="1 - 5")
        factories.Answer(
            response=response1, question=self.poll1_question2,
            value="It's very rainy", category="All Responses")

        response2 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=234, contact='C-002', created_on=timezone.now()))
        factories.Answer(
            response=response2, question=self.poll1_question1,
            value="3.00000", category="1 - 5")
        factories.Answer(
            response=response2, question=self.poll1_question2,
            value="rainy and rainy", category="All Responses")

        response3 = Response.create_empty(
            self.unicef, self.pollrun,
            Run.create(id=345, contact='C-004', created_on=timezone.now()))
        factories.Answer(
            response=response3, question=self.poll1_question1,
            value="8.00000", category="6 - 10")
        factories.Answer(
            response=response3, question=self.poll1_question2,
            value="Sunny sunny", category="All Responses")

        # Set all responses to COMPLETE so that they can be found in charting functions
        Response.objects.all().update(status=Response.STATUS_COMPLETE)

    def test_multiple_pollruns_non_numeric(self):

        pollruns = PollRun.objects.filter(pk=self.pollrun.pk)
        regions = []

        # Test TYPE_MULTIPLE_CHOICE data from question 1
        question = self.poll1_question1

        # TYPE_MULTIPLE_CHOICE should return
        # A list with single date (today) for the single pollrun
        # An ordered dictionary
        date_list, pollrun_dict = multiple_pollruns_non_numeric(
            pollruns, question, regions)

        self.assertEqual(
            date_list,
            [timezone.now().date()])
        self.assertEqual(
            pollrun_dict,
            OrderedDict([(u'1 - 5', [2]), (u'6 - 10', [1]), (None, [3])]))

        # Test TYPE_OPEN data from question 2
        question = self.poll1_question2

        # TYPE_OPEN should return
        # An empty date_list (no dates associated with wordcloud data)
        # A json string with words and weights
        date_list, pollrun_dict = multiple_pollruns_non_numeric(
            pollruns, question, regions)

        self.assertEqual(
            len(date_list),
            0)
        self.assertEqual(
            pollrun_dict,
            '[{"text": "rainy", "weight": 3}, {"text": "sunny", "weight": 2}]')
