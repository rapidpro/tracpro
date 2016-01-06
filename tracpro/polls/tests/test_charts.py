from collections import OrderedDict

from django.utils import timezone

from temba_client.types import Run

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import PollRun, Question, Response
from ..charts import multiple_pollruns_non_numeric, multiple_pollruns_numeric


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

    def test_multiple_pollruns_non_numeric(self):

        # Test TYPE_MULTIPLE_CHOICE data from question 1
        question = self.poll1_question1

        # TYPE_MULTIPLE_CHOICE should return
        # A list with single date (today) for the single pollrun
        # An ordered dictionary
        date_list, pollrun_dict = multiple_pollruns_non_numeric(
            self.pollruns, question, self.regions)

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
            self.pollruns, question, self.regions)

        self.assertEqual(
            len(date_list),
            0)
        self.assertEqual(
            pollrun_dict,
            '[{"text": "rainy", "weight": 3}, {"text": "sunny", "weight": 2}]')

    def test_multiple_pollruns_numeric(self):
        # Reset question 1 type to NUMERIC
        # Answers are 4, 3 and 8 for a single date (today)

        self.poll1_question1.question_type = Question.TYPE_NUMERIC
        self.poll1_question1.save()
        (answer_sum_dict_list,
         answer_average_dict_list,
         response_rate_dict_list,
         date_list,
         answer_mean,
         answer_stdev,
         response_rate_average,
         pollrun_list) = multiple_pollruns_numeric(
            self.pollruns, self.poll1_question1, self.regions)

        # Single item for single date: sum = 4 + 3 + 8 = 15
        # URL points to pollrun detail page for this date
        self.assertEqual(
            answer_sum_dict_list,
            '[{"y": 15.0, "url": "/pollrun/read/' + str(self.pollrun.pk) + '/"}]')

        # Single item for single date: average = (4 + 3 + 8)/3 = 5
        # URL points to pollrun detail page for this date
        self.assertEqual(
            answer_average_dict_list,
            '[{"y": 5.0, "url": "/pollrun/read/' + str(self.pollrun.pk) + '/"}]')

        # Set all responses to complete in setUp()
        # Response rate = 100%
        # URL points to participation tab
        self.assertEqual(
            response_rate_dict_list,
            '[{"y": 100.0, "url": "/pollrun/participation/' + str(self.pollrun.pk) + '/"}]')

        # Today's date
        self.assertEqual(
            date_list,
            [timezone.now().date()])

        # Mean, Standard Dev, response rate avg, pollrun list
        self.assertEqual(
            answer_mean,
            5.0)
        self.assertEqual(
            answer_stdev,
            0.0)
        self.assertEqual(
            response_rate_average,
            100.0)
        self.assertEqual(
            pollrun_list,
            [self.pollrun.pk])

        # Set one of the responses to partial, changing the response rate
        Response.objects.filter(contact=self.contact1).update(status=Response.STATUS_PARTIAL)
        (answer_sum_dict_list,
         answer_average_dict_list,
         response_rate_dict_list,
         date_list,
         answer_mean,
         answer_stdev,
         response_rate_average,
         pollrun_list) = multiple_pollruns_numeric(
            self.pollruns, self.poll1_question1, self.regions)

        # 2 complete responses, 1 partial response
        # Response rate = 66.67%
        self.assertEqual(
            response_rate_dict_list,
            '[{"y": 66.67, "url": "/pollrun/participation/' + str(self.pollrun.pk) + '/"}]')
        self.assertEqual(
            response_rate_average,
            66.67)
