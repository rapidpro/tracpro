# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime

from mock import patch

import pytz

from temba.types import Flow, RuleSet, Run, RunValueSet

from django.utils import timezone

from tracpro.test.cases import TracProDataTest

from ..models import Answer, Poll, PollRun, Response
from . import factories


class PollTest(TracProDataTest):

    @patch('dash.orgs.models.TembaClient.get_flows')
    def test_sync_with_flows(self, mock_get_flows):
        mock_get_flows.return_value = [
            Flow.create(name="Poll #3", uuid='F-003', rulesets=[
                RuleSet.create(uuid='RS-004', label='How old are you', response_type='C'),
                RuleSet.create(uuid='RS-005', label='Where do you live', response_type='O')
            ]),
            Flow.create(name="Poll #4", uuid='F-004', rulesets=[
                RuleSet.create(uuid='RS-006', label='How many goats', response_type='N'),
                RuleSet.create(uuid='RS-007', label='How many sheep', response_type='N')
            ]),
            Flow.create(name="Poll #5", uuid='F-005', rulesets=[
                RuleSet.create(uuid='RS-008', label='What time is it', response_type='O')
            ])
        ]
        Poll.sync_with_flows(self.unicef, ['F-003', 'F-004'])

        self.assertEqual(self.unicef.polls.filter(is_active=True).count(), 2)

        # existing poll that wasn't included should now be inactive
        self.assertFalse(Poll.objects.get(flow_uuid='F-001').is_active)

        poll3 = Poll.objects.get(flow_uuid='F-003')
        self.assertEqual(poll3.name, "Poll #3")
        self.assertEqual(poll3.questions.count(), 2)
        self.assertEqual(str(poll3), "Poll #3")

        # switch back to flow #1
        mock_get_flows.return_value = [
            Flow.create(name="Poll #1", uuid='F-001', rulesets=[
                RuleSet.create(uuid='RS-001', label='Number of sheep', response_type='N'),
                RuleSet.create(uuid='RS-002', label='Number of goats', response_type='N')
            ])
        ]

        Poll.sync_with_flows(self.unicef, ['F-001'])

        # existing poll that was inactive should now be active
        self.assertTrue(Poll.objects.get(flow_uuid='F-001').is_active)

    def test_get_questions(self):
        self.assertEqual(
            list(self.poll1.get_questions()),
            [self.poll1_question1, self.poll1_question2])
        self.assertEqual(
            list(self.poll2.get_questions()),
            [self.poll2_question1])


class PollRunTest(TracProDataTest):

    def test_get_or_create_universal(self):
        # 2014-Jan-01 04:30 in org's Afg timezone
        with patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc)
            # no existing pollruns so one is created
            pollrun1 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(
                pollrun1.conducted_on,
                datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc))

        # 2014-Jan-01 23:30 in org's Afg timezone
        with patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 19, 0, 0, 0, pytz.utc)
            # existing pollrun on same day is returned
            pollrun2 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(pollrun1, pollrun2)

        # 2014-Jan-02 00:30 in org's Afg timezone
        with patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc)
            # different day locally so new pollrun
            pollrun3 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertNotEqual(pollrun3, pollrun1)
            self.assertEqual(
                pollrun3.conducted_on,
                datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc))

        # 2014-Jan-02 04:30 in org's Afg timezone
        with patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.utc)
            # same day locally so no new pollrun
            pollrun4 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(pollrun3, pollrun4)

    def test_completion(self):
        date1 = self.datetime(2014, 1, 1, 7, 0)

        # pollrun with no responses (complete or incomplete) has null completion
        pollrun = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=date1)

        # add a incomplete response from contact in region #1
        response1 = factories.Response(
            pollrun=pollrun, contact=self.contact1,
            created_on=date1, updated_on=date1, status=Response.STATUS_EMPTY)

        self.assertEqual(list(pollrun.get_responses()), [response1])
        self.assertDictEqual(pollrun.get_response_counts(), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 0,
        })

        self.assertEqual(list(pollrun.get_responses(self.region1)), [response1])
        self.assertDictEqual(pollrun.get_response_counts(self.region1), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 0,
        })

        self.assertEqual(list(pollrun.get_responses(self.region2)), [])
        self.assertDictEqual(pollrun.get_response_counts(self.region2), {
            Response.STATUS_EMPTY: 0,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 0,
        })

        # add a complete response from another contact in region #1
        response2 = factories.Response(
            pollrun=pollrun, contact=self.contact2,
            created_on=date1, updated_on=date1, status=Response.STATUS_COMPLETE)

        self.assertEqual(
            list(pollrun.get_responses().order_by('pk')),
            [response1, response2])
        self.assertDictEqual(pollrun.get_response_counts(), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 1,
        })

        self.assertEqual(
            list(pollrun.get_responses(self.region1).order_by('pk')),
            [response1, response2])
        self.assertDictEqual(pollrun.get_response_counts(self.region1), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 1,
        })

        self.assertEqual(list(pollrun.get_responses(self.region2)), [])
        self.assertDictEqual(pollrun.get_response_counts(self.region2), {
            Response.STATUS_EMPTY: 0,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 0,
        })

        # add a complete response from contact in different region
        response3 = factories.Response(
            pollrun=pollrun, contact=self.contact4,
            created_on=date1, updated_on=date1, status=Response.STATUS_COMPLETE)

        self.assertEqual(
            list(pollrun.get_responses().order_by('pk')),
            [response1, response2, response3])
        self.assertDictEqual(pollrun.get_response_counts(), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 2,
        })

        self.assertEqual(
            list(pollrun.get_responses(self.region1).order_by('pk')),
            [response1, response2])
        self.assertDictEqual(pollrun.get_response_counts(self.region1), {
            Response.STATUS_EMPTY: 1,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 1,
        })

        self.assertEqual(
            list(pollrun.get_responses(self.region2)),
            [response3])
        self.assertDictEqual(pollrun.get_response_counts(self.region2), {
            Response.STATUS_EMPTY: 0,
            Response.STATUS_PARTIAL: 0,
            Response.STATUS_COMPLETE: 1,
        })

    def test_is_last_for_region(self):
        pollrun1 = factories.RegionalPollRun(
            poll=self.poll1, region=self.region1, conducted_on=timezone.now())
        pollrun2 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())
        pollrun3 = factories.RegionalPollRun(
            poll=self.poll1, region=self.region2, conducted_on=timezone.now())

        # pollrun #2 covers region #1 and is newer
        self.assertFalse(pollrun1.is_last_for_region(self.region1))
        # pollrun #1 didn't cover region #2
        self.assertFalse(pollrun1.is_last_for_region(self.region2))
        self.assertTrue(pollrun2.is_last_for_region(self.region1))
        # pollrun #3 covers region #2 and is newer
        self.assertFalse(pollrun2.is_last_for_region(self.region2))
        self.assertTrue(pollrun3.is_last_for_region(self.region2))

    def test_answer_aggregation(self):
        self.contact5.language = 'ara'
        self.contact5.save()

        pollrun = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())

        response1 = Response.create_empty(
            self.unicef, pollrun,
            Run.create(id=123, contact='C-001', created_on=timezone.now()))
        factories.Answer(
            response=response1, question=self.poll1_question1,
            value="4.00000", category="1 - 5")
        factories.Answer(
            response=response1, question=self.poll1_question2,
            value="It's very rainy", category="All Responses")

        response2 = Response.create_empty(
            self.unicef, pollrun,
            Run.create(id=234, contact='C-002', created_on=timezone.now()))
        factories.Answer(
            response=response2, question=self.poll1_question1,
            value="3.00000", category="1 - 5")
        factories.Answer(
            response=response2, question=self.poll1_question2,
            value="rainy and rainy", category="All Responses")

        response3 = Response.create_empty(
            self.unicef, pollrun,
            Run.create(id=345, contact='C-004', created_on=timezone.now()))
        factories.Answer(
            response=response3, question=self.poll1_question1,
            value="8.00000", category="6 - 10")
        factories.Answer(
            response=response3, question=self.poll1_question2,
            value="Sunny sunny", category="All Responses")

        response4 = Response.create_empty(
            self.unicef, pollrun,
            Run.create(id=456, contact='C-005', created_on=timezone.now()))
        factories.Answer(
            response=response4, question=self.poll1_question2,
            value="مطر", category="All Responses")

        # category counts for question #1
        self.assertEqual(
            pollrun.get_answer_category_counts(self.poll1_question1),
            [("1 - 5", 2), ("6 - 10", 1)])
        self.assertEqual(
            pollrun.get_answer_category_counts(
                self.poll1_question1,
                [self.region1]),
            [("1 - 5", 2)])
        self.assertEqual(
            pollrun.get_answer_category_counts(
                self.poll1_question1,
                [self.region2]),
            [("6 - 10", 1)])
        self.assertEqual(
            pollrun.get_answer_category_counts(
                self.poll1_question1,
                [self.region3]),
            [])

        # and from cache... (lists rather than tuples due to JSON serialization)
        with self.assertNumQueries(0):
            self.assertEqual(
                pollrun.get_answer_category_counts(
                    self.poll1_question1),
                [["1 - 5", 2], ["6 - 10", 1]])
            self.assertEqual(
                pollrun.get_answer_category_counts(
                    self.poll1_question1,
                    [self.region1]),
                [["1 - 5", 2]])
            self.assertEqual(
                pollrun.get_answer_category_counts(
                    self.poll1_question1,
                    [self.region2]),
                [["6 - 10", 1]])
            self.assertEqual(
                pollrun.get_answer_category_counts(
                    self.poll1_question1,
                    [self.region3]),
                [])

        # auto-range category counts for question #1
        self.assertEqual(
            pollrun.get_answer_auto_range_counts(self.poll1_question1),
            [('2 - 3', 1), ('4 - 5', 1), ('6 - 7', 0), ('8 - 9', 1), ('10 - 11', 0)])
        self.assertEqual(
            pollrun.get_answer_auto_range_counts(
                self.poll1_question1,
                [self.region1]),
            [('3', 1), ('4', 1), ('5', 0), ('6', 0), ('7', 0)])
        self.assertEqual(
            pollrun.get_answer_auto_range_counts(
                self.poll1_question1,
                [self.region2]),
            [('8', 1), ('9', 0), ('10', 0), ('11', 0), ('12', 0)])
        self.assertEqual(
            pollrun.get_answer_auto_range_counts(
                self.poll1_question1,
                [self.region3]),
            [])

        # numeric averages for question #1
        self.assertEqual(
            pollrun.get_answer_numeric_average(self.poll1_question1), 5.0)
        self.assertEqual(
            pollrun.get_answer_numeric_average(
                self.poll1_question1,
                [self.region1]), 3.5)
        self.assertEqual(
            pollrun.get_answer_numeric_average(
                self.poll1_question1,
                [self.region2]), 8.0)
        self.assertEqual(
            pollrun.get_answer_numeric_average(
                self.poll1_question1,
                [self.region3]), 0.0)

        # word counts for question #2
        self.assertEqual(
            pollrun.get_answer_word_counts(self.poll1_question2),
            [("rainy", 3), ("sunny", 2), ('مطر', 1)])
        self.assertEqual(
            pollrun.get_answer_word_counts(
                self.poll1_question2,
                [self.region1]),
            [("rainy", 3)])
        self.assertEqual(
            pollrun.get_answer_word_counts(
                self.poll1_question2,
                [self.region2]),
            [("sunny", 2)])
        self.assertEqual(
            pollrun.get_answer_word_counts(
                self.poll1_question2,
                [self.region3]),
            [('مطر', 1)])


class ResponseTest(TracProDataTest):

    def test_from_run(self):
        # a complete run
        run = Run.create(
            id=1234,
            flow='F-001',  # flow UUID for poll #1
            contact='C-001',
            completed=True,
            values=[
                RunValueSet.create(
                    category="1 - 50",
                    node='RS-001',
                    text="6",
                    value="6.00000000",
                    label="Number of sheep",
                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC)
                ),
                RunValueSet.create(
                    category="1 - 25",
                    node='RS-002',
                    text="4",
                    value="4.00000000",
                    label="Number of goats",
                    time=datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC),
                ),
            ],
            steps=[],  # not used
            created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC),
        )

        response1 = Response.from_run(self.unicef, run)
        self.assertEqual(response1.contact, self.contact1)
        self.assertEqual(
            response1.created_on,
            datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(
            response1.updated_on,
            datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response1.status, Response.STATUS_COMPLETE)
        self.assertEqual(len(response1.answers.all()), 2)
        answers = list(response1.answers.order_by('question_id'))
        self.assertEqual(answers[0].question, self.poll1_question1)
        self.assertEqual(answers[0].value, "6.00000000")
        self.assertEqual(answers[0].category, "1 - 50")
        self.assertEqual(
            answers[0].submitted_on,
            datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(answers[1].question, self.poll1_question2)
        self.assertEqual(answers[1].value, "4.00000000")
        self.assertEqual(answers[1].category, "1 - 25")
        self.assertEqual(
            answers[1].submitted_on,
            datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))

        # an partially complete run
        run = Run.create(
            id=2345,
            flow='F-001',  # flow UUID for poll #1
            contact='C-002',
            completed=False,
            values=[
                RunValueSet.create(
                    category="1 - 50",
                    node='RS-001',
                    text="6",
                    value="6.00000000",
                    label="Number of sheep",
                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC),
                ),
            ],
            steps=[],  # not used
            created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC),
        )

        response2 = Response.from_run(self.unicef, run)
        self.assertEqual(response2.contact, self.contact2)
        self.assertEqual(
            response2.created_on,
            datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(
            response2.updated_on,
            datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response2.status, Response.STATUS_PARTIAL)
        self.assertEqual(len(response2.answers.all()), 1)

        # now completed
        run = Run.create(
            id=2345,
            flow='F-001',  # flow UUID for poll #1
            contact='C-002',
            completed=True,
            values=[
                RunValueSet.create(
                    category="1 - 50",
                    node='RS-001',
                    text="6",
                    value="6.00000000",
                    label="Number of sheep",
                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC),
                ),
                RunValueSet.create(
                    category="1 - 25",
                    node='RS-002',
                    text="4",
                    value="4.00000000",
                    label="Number of goats",
                    time=datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC),
                ),
            ],
            steps=[],  # not used
            created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC),
        )

        response3 = Response.from_run(self.unicef, run)
        self.assertEqual(response3.contact, self.contact2)
        self.assertEqual(
            response3.created_on,
            datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(
            response3.updated_on,
            datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response3.status, Response.STATUS_COMPLETE)
        self.assertEqual(len(response3.answers.all()), 2)

        # an empty run
        run = Run.create(
            id=3456,
            flow='F-001',  # flow UUID for poll #1
            contact='C-003',
            completed=False,
            values=[],
            steps=[],  # not used
            created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC),
        )

        response4 = Response.from_run(self.unicef, run)
        self.assertEqual(response4.contact, self.contact3)
        self.assertEqual(
            response4.created_on,
            datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(
            response4.updated_on,
            datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response4.status, Response.STATUS_EMPTY)
        self.assertEqual(len(response4.answers.all()), 0)

        # new run for same contact should de-activate old response
        run = Run.create(
            id=4567,
            flow='F-001',  # flow UUID for poll #1
            contact='C-003',
            completed=False,
            values=[],
            steps=[],  # not used
            created_on=datetime.datetime(2013, 1, 2, 3, 0, 0, 0, pytz.UTC),
        )

        response5 = Response.from_run(self.unicef, run)
        self.assertFalse(Response.objects.get(pk=response4.pk).is_active)
        self.assertEqual(response5.contact, self.contact3)

        # same run if we call again
        self.assertEqual(Response.from_run(self.unicef, run), response5)


class AnswerTest(TracProDataTest):

    def test_create(self):
        pollrun = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())
        response = Response.create_empty(
            self.unicef, pollrun,
            Run.create(id=123, contact='C-001', created_on=timezone.now()))

        answer1 = factories.Answer(
            response=response, question=self.poll1_question1,
            value="4.00000", category="1 - 5")
        self.assertEqual(answer1.response, response)
        self.assertEqual(answer1.question, self.poll1_question1)
        self.assertEqual(answer1.category, "1 - 5")
        self.assertEqual(answer1.value, "4.00000")

        answer2 = factories.Answer(
            response=response, question=self.poll1_question1,
            value="rain", category=dict(base="Rain", rwa="Imvura"))
        self.assertEqual(answer2.category, "Rain")

        answer3 = factories.Answer(
            response=response, question=self.poll1_question1,
            value="rain", category=dict(eng="Yes"))
        self.assertEqual(answer3.category, "Yes")

    def test_auto_range_counts(self):
        qs = Answer.objects.none()
        self.assertEqual(qs.auto_range_counts(), {})

    def test_auto_range_counts_2(self):
        a = factories.Answer(value=1, category=None)
        qs = Answer.objects.filter(pk=a.pk)
        self.assertEqual(qs.auto_range_counts(), {})

    def test_auto_range_counts_3(self):
        a = factories.Answer(value=1, category="1 - 100")
        qs = Answer.objects.filter(pk=a.pk)
        self.assertEqual(
            qs.auto_range_counts(),
            {'1': 1, '2': 0, '3': 0, '4': 0, '5': 0})

    def test_auto_range_counts_4(self):
        a1 = factories.Answer(value=1, category="1 - 100")
        a2 = factories.Answer(value=2, category="1 - 100")
        a3 = factories.Answer(value=2, category="1 - 100")
        a4 = factories.Answer(value=3, category="1 - 100")
        qs = Answer.objects.filter(pk__in=[a1.pk, a2.pk, a3.pk, a4.pk])
        self.assertEqual(
            qs.auto_range_counts(),
            {'1': 1, '2': 2, '3': 1, '4': 0, '5': 0})

    def test_auto_range_counts_5(self):
        a1 = factories.Answer(value=1, category="1 - 100")
        a2 = factories.Answer(value=2, category="1 - 100")
        a3 = factories.Answer(value=6, category="1 - 100")
        a4 = factories.Answer(value=6, category="1 - 100")
        a5 = factories.Answer(value=13, category="1 - 100")
        qs = Answer.objects.filter(pk__in=[a1.pk, a2.pk, a3.pk, a4.pk, a5.pk])
        self.assertEqual(
            qs.auto_range_counts(),
            {'0 - 9': 4, '10 - 19': 1, '20 - 29': 0, '30 - 39': 0, '40 - 49': 0})

    def test_numeric_average(self):
        qs = Answer.objects.none()
        self.assertEqual(qs.numeric_average(), 0)

    def test_numeric_average_2(self):
        a = factories.Answer(value=1, category=None)
        qs = Answer.objects.filter(pk=a.pk)
        self.assertEqual(qs.numeric_average(), 0)

    def test_numeric_average_3(self):
        a = factories.Answer(value=1, category="1 - 100")
        qs = Answer.objects.filter(pk=a.pk)
        self.assertEqual(qs.numeric_average(), 1)

    def test_numeric_average_4(self):
        a1 = factories.Answer(value=1, category="1 - 100")
        a2 = factories.Answer(value=2, category="1 - 100")
        qs = Answer.objects.filter(pk__in=[a1.pk, a2.pk])
        self.assertEqual(qs.numeric_average(), 1.5)
