from __future__ import unicode_literals

from django.core.urlresolvers import reverse

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import charts
from .. import models


class PollChartTest(TracProTest):

    def setUp(self):
        super(PollChartTest, self).setUp()

        self.org = factories.Org()

        self.poll = factories.Poll(org=self.org)

        self.region1 = factories.Region(org=self.org, name="Beta")
        self.region2 = factories.Region(org=self.org, name="Acme")

        self.question1 = factories.Question(
            poll=self.poll, question_type=models.Question.TYPE_MULTIPLE_CHOICE)
        self.question2 = factories.Question(
            poll=self.poll, question_type=models.Question.TYPE_OPEN)
        self.question3 = factories.Question(
            poll=self.poll, question_type=models.Question.TYPE_NUMERIC)

        self.pollrun = factories.UniversalPollRun(poll=self.poll)

        self.contact1 = factories.Contact(org=self.org, region=self.region1)
        self.response1 = factories.Response(
            contact=self.contact1, pollrun=self.pollrun,
            status=models.Response.STATUS_COMPLETE)
        factories.Answer(
            response=self.response1, question=self.question1,
            value="4.00000", category="1 - 5")
        factories.Answer(
            response=self.response1, question=self.question2,
            value="It's very rainy", category="All Responses")
        factories.Answer(
            response=self.response1, question=self.question3,
            value="4.00000", category="1 - 5")

        self.contact2 = factories.Contact(org=self.org, region=self.region1)
        self.response2 = factories.Response(
            contact=self.contact2, pollrun=self.pollrun,
            status=models.Response.STATUS_COMPLETE)
        factories.Answer(
            response=self.response2, question=self.question1,
            value="3.00000", category="1 - 5")
        factories.Answer(
            response=self.response2, question=self.question2,
            value="rainy and rainy", category="All Responses")
        factories.Answer(
            response=self.response2, question=self.question3,
            value="3.00000", category="1 - 5")

        self.contact3 = factories.Contact(org=self.org, region=self.region2)
        self.response3 = factories.Response(
            contact=self.contact3, pollrun=self.pollrun,
            status=models.Response.STATUS_COMPLETE)
        factories.Answer(
            response=self.response3, question=self.question1,
            value="8.00000", category="6 - 10")
        factories.Answer(
            response=self.response3, question=self.question2,
            value="Sunny sunny", category="All Responses")
        factories.Answer(
            response=self.response3, question=self.question3,
            value="8.00000", category="6 - 10")

        self.pollruns = models.PollRun.objects.filter(pk=self.pollrun.pk)
        self.responses = models.Response.objects.filter(pollrun=self.pollrun)

    def test_multiple_pollruns_multiple_choice(self):
        answers = models.Answer.objects.filter(question=self.question1)
        data, summary_table = charts.multiple_pollruns_multiple_choice(
            self.pollruns, answers, self.responses, contact_filters={})

        self.assertEqual(
            data['dates'],
            [self.pollrun.conducted_on.strftime('%Y-%m-%d')])
        self.assertEqual(data['series'], [
            {'name': '1 - 5',
             'data': [{'y': 2, 'url': reverse('polls.pollrun_read', args=[self.pollrun.pk])}]},
            {'name': '6 - 10',
             'data': [{'y': 1, 'url': reverse('polls.pollrun_read', args=[self.pollrun.pk])}]},
        ])

    def test_word_cloud_data(self):
        answers = models.Answer.objects.filter(question=self.question2)
        data = charts.word_cloud_data(answers)
        self.assertEqual(data, [
            {"text": "rainy", "weight": 3},
            {"text": "sunny", "weight": 2},
        ])

    def test_multiple_pollruns_numeric(self):
        chart_type, data, summary_table = charts.multiple_pollruns(
            self.pollruns, self.responses, self.question3, split_regions=False,
            contact_filters={})
        summary_data = dict(summary_table)

        self.assertEqual(chart_type, "numeric")

        self.assertEqual(data['pollrun-urls'], [
            reverse('polls.pollrun_read', args=[self.pollrun.pk]),
        ])
        self.assertEqual(data['participation-urls'], [
            reverse('polls.pollrun_participation', args=[self.pollrun.pk]),
        ])

        # Answers are 4, 3 and 8 for a single date

        # Single item for single date: sum = 4 + 3 + 8 = 15
        # URL points to pollrun detail page for this date
        self.assertEqual(data['sum'], [{
            'name': self.question3.name,
            'data': [15.0],
        }])

        # Single item for single date: average = (4 + 3 + 8)/3 = 5
        # URL points to pollrun detail page for this date
        self.assertEqual(data['average'], [{
            'name': self.question3.name,
            'data': [5.0],
        }])

        # Set all responses to complete in setUp()
        # Response rate = 100%
        # URL points to participation tab
        self.assertEqual(data['response-rate'], [{
            'name': self.question3.name,
            'data': [100.0],
        }])

        # Today's date
        self.assertEqual(
            data['dates'],
            [self.pollrun.conducted_on.strftime('%Y-%m-%d')])

        # Mean, Standard Dev, response rate avg, pollrun list
        self.assertEqual(summary_data['Mean'], 5.0)
        self.assertEqual(summary_data['Standard deviation'], 0.0)
        self.assertEqual(summary_data['Response rate average (%)'], 100.0)

        # Remove an answer, thus changing the response rate.
        self.response1.answers.get(question=self.question3).delete()

        chart_type, data, summary_table = charts.multiple_pollruns(
            self.pollruns, self.responses, self.question3, split_regions=False,
            contact_filters={})
        summary_data = dict(summary_table)

        self.assertEqual(chart_type, "numeric")

        # 2 answers of 3 expected - response rate should be 66.7%
        self.assertEqual(data['response-rate'], [{
            'name': self.question3.name,
            'data': [66.7],
        }])
        self.assertEqual(summary_data['Response rate average (%)'], 66.7)

    def test_multiple_pollruns_numeric_split(self):
        chart_type, data, summary_table = charts.multiple_pollruns(
            self.pollruns, self.responses, self.question3, split_regions=True,
            contact_filters={})
        summary_data = dict(summary_table)

        self.assertEqual(chart_type, "numeric")

        self.assertEqual(data['pollrun-urls'], [
            reverse('polls.pollrun_read', args=[self.pollrun.pk]),
        ])
        self.assertEqual(data['participation-urls'], [
            reverse('polls.pollrun_participation', args=[self.pollrun.pk]),
        ])

        self.assertEqual(data['sum'], [
            {
                'name': "Acme",
                'data': [8.0],
            },
            {
                'name': "Beta",
                'data': [7.0],
            },
        ])

        # Single item for single date: average = (4 + 3 + 8)/3 = 5
        # URL points to pollrun detail page for this date
        self.assertEqual(data['average'], [
            {
                'name': "Acme",
                'data': [8.0],
            },
            {
                'name': "Beta",
                'data': [3.5],
            },
        ])

        # Set all responses to complete in setUp()
        # Response rate = 100%
        # URL points to participation tab
        self.assertEqual(data['response-rate'], [
            {
                'name': "Acme",
                'data': [100.0],
            },
            {
                'name': "Beta",
                'data': [100.0],
            },
        ])

        # Today's date
        self.assertEqual(
            data['dates'],
            [self.pollrun.conducted_on.strftime('%Y-%m-%d')])

        self.assertEqual(summary_data['Mean'], 5.0)
        self.assertEqual(summary_data['Standard deviation'], 0.0)
        self.assertEqual(summary_data['Response rate average (%)'], 100.0)

    def test_single_pollrun_multiple_choice(self):
        answers = models.Answer.objects.filter(question=self.question1)
        data = charts.single_pollrun_multiple_choice(answers, self.pollrun)

        self.assertEqual(
            data['data'],
            [2, 1])
        self.assertEqual(
            data['categories'],
            ['1 - 5', '6 - 10'])

    def test_single_pollrun_open(self):
        chart_type, chart_data, summary_table = charts.single_pollrun(
            self.pollrun, self.responses, self.question2)

        self.assertEqual(chart_type, 'open-ended')
        self.assertEqual(chart_data[0], {'text': 'rainy', 'weight': 3})
        self.assertEqual(len(chart_data), 2)
        self.assertEqual(summary_table, None)

    def test_single_pollrun_numeric(self):
        # Make answers numeric
        self.question3.question_type = models.Question.TYPE_NUMERIC
        self.question3.save()
        # Answers for question 3 = 8, 3 and 4
        # Average = 5, Response Rate = 100%, STDEV = 2.2
        chart_type, chart_data, summary_table = charts.single_pollrun(
            self.pollrun, self.responses, self.question3)
        summary_data = dict(summary_table)

        self.assertEqual(chart_type, 'bar')
        self.assertEqual(summary_data['Mean'], 5)
        self.assertEqual(summary_data['Response rate average (%)'], 100)
        self.assertEqual(summary_data['Standard deviation'], 2.2)

        # Results are autocategorized
        self.assertEqual([2, 1], chart_data['data'])
        self.assertEqual(2, len(chart_data['categories']))
