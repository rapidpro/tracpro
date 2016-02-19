# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime
import json

import mock

import pytz

from temba_client.types import Run, RunValueSet

from django.db import IntegrityError
from django.utils import timezone

from tracpro.test import factories
from tracpro.test.cases import TracProTest, TracProDataTest

from ..models import Answer, Poll, PollRun, Response
from .. import models


class TestPollQuerySet(TracProTest):

    def test_active(self):
        """active filter shouldn't return Polls where is_active is False."""
        poll = factories.Poll(is_active=True)
        factories.Poll(is_active=False)
        self.assertEqual(list(models.Poll.objects.active()), [poll])

    def test_by_org(self):
        """by_org filter should return only Polls for the given org."""
        org = factories.Org()
        poll = factories.Poll(org=org)
        factories.Poll()
        self.assertEqual(list(models.Poll.objects.by_org(org)), [poll])


class TestPollManager(TracProTest):

    def test_set_active_for_org(self):
        """Set which org polls are active."""
        polls = []

        org = factories.Org()
        polls.append(factories.Poll(org=org, is_active=True, flow_uuid='0'))
        polls.append(factories.Poll(org=org, is_active=True, flow_uuid='1'))
        polls.append(factories.Poll(org=org, is_active=False, flow_uuid='2'))
        polls.append(factories.Poll(org=org, is_active=False, flow_uuid='3'))

        other_org = factories.Org()
        polls.append(factories.Poll(org=other_org, is_active=True, flow_uuid='4'))
        polls.append(factories.Poll(org=other_org, is_active=False, flow_uuid='5'))

        models.Poll.objects.set_active_for_org(org, ['0', '2'])

        # Refresh from database.
        polls = [models.Poll.objects.get(pk=p.pk) for p in polls]

        # Specified org Polls should be active.
        self.assertTrue(polls[0].is_active)
        self.assertTrue(polls[2].is_active)

        # All other org polls should be inactive.
        self.assertFalse(polls[1].is_active)
        self.assertFalse(polls[3].is_active)

        # Polls for other orgs should be unaffected.
        self.assertTrue(polls[4].is_active)
        self.assertFalse(polls[5].is_active)

    def test_set_active_for_org__invalid_uuids(self):
        """An error is raised when an invalid UUID for the org is passed."""
        org = factories.Org()
        poll = factories.Poll(org=org, is_active=False, flow_uuid='a')

        other_org = factories.Org()
        other_poll = factories.Poll(org=other_org, is_active=False, flow_uuid='b')

        with self.assertRaises(ValueError):
            Poll.objects.set_active_for_org(org, ['a', 'b'])

        poll.refresh_from_db()
        self.assertFalse(poll.is_active)
        other_poll.refresh_from_db()
        self.assertFalse(other_poll.is_active)

    def test_from_temba__existing(self):
        """Fields on an existing Poll should be updated from RapidPro."""
        org = factories.Org()
        poll = factories.Poll(
            org=org, flow_uuid='abc', rapidpro_name='old', name='custom',
            is_active=True)
        flow = factories.TembaFlow(uuid='abc', name='new')

        updated = Poll.objects.from_temba(org, flow)

        poll.refresh_from_db()
        self.assertEqual(poll.pk, updated.pk)
        self.assertEqual(poll.rapidpro_name, 'new')
        self.assertEqual(poll.name, 'custom')
        self.assertTrue(poll.is_active)

    def test_from_temba__new_active(self):
        """A new inactive Poll should be created to match RapidPro data."""
        org = factories.Org()
        flow = factories.TembaFlow()

        poll = Poll.objects.from_temba(org, flow)

        self.assertEqual(poll.flow_uuid, flow.uuid)
        self.assertEqual(poll.rapidpro_name, flow.name)
        self.assertEqual(poll.name, flow.name)
        self.assertFalse(poll.is_active)

    def test_sync__delete_non_existant_poll(self):
        """Sync should delete Polls that track a flow that does not exist."""
        org = factories.Org()
        poll = factories.Poll(org=org)  # noqa
        self.mock_temba_client.get_flows.return_value = []
        models.Poll.objects.sync(org)

        self.assertEqual(models.Poll.objects.count(), 0)

    def test_sync__delete_non_existant_question(self):
        org = factories.Org()
        poll = factories.Poll(org=org)
        question = factories.Question(poll=poll)  # noqa
        flow = factories.TembaFlow(uuid=poll.flow_uuid)  # no questions
        self.mock_temba_client.get_flows.return_value = [flow]
        models.Poll.objects.sync(org)

        self.assertEqual(models.Poll.objects.count(), 1)
        self.assertEqual(models.Question.objects.count(), 0)

    @mock.patch('tracpro.polls.models.Question.objects.from_temba')
    def test_sync__add_new(self, mock_question_from_temba):
        """Sync should create an inactive poll to track a new flow."""
        org = factories.Org()
        flow = factories.TembaFlow()
        ruleset = factories.TembaRuleSet()
        flow.rulesets = [ruleset]
        self.mock_temba_client.get_flows.return_value = [flow]
        models.Poll.objects.sync(org)

        self.assertEqual(models.Poll.objects.count(), 1)
        poll = models.Poll.objects.get()
        self.assertFalse(poll.is_active)
        self.assertEqual(poll.rapidpro_name, flow.name)
        self.assertEqual(poll.name, flow.name)

        self.assertEqual(mock_question_from_temba.call_count, 1)

    def test_sync__update_existing(self):
        """Sync should update existing objects if they have changed on RapidPro."""
        self.mock_temba_client.get_flow_definition.return_value = factories.TembaFlowDefinition()

        org = factories.Org()
        poll = factories.Poll(org=org, is_active=True)
        question = factories.Question(poll=poll)
        flow = factories.TembaFlow(uuid=poll.flow_uuid)
        ruleset = factories.TembaRuleSet(uuid=question.ruleset_uuid)
        flow.rulesets = [ruleset]
        self.mock_temba_client.get_flows.return_value = [flow]
        models.Poll.objects.sync(org)

        self.assertEqual(models.Poll.objects.count(), 1)
        poll = models.Poll.objects.get()
        self.assertEqual(poll.org, org)
        self.assertEqual(poll.flow_uuid, flow.uuid)
        self.assertEqual(poll.rapidpro_name, flow.name)
        self.assertEqual(poll.name, flow.name)
        self.assertTrue(poll.is_active)

        self.assertEqual(models.Question.objects.count(), 1)
        question = models.Question.objects.get()
        self.assertEqual(question.poll, poll)
        self.assertEqual(question.ruleset_uuid, ruleset.uuid)
        self.assertEqual(question.rapidpro_name, ruleset.label)
        self.assertEqual(question.name, ruleset.label)
        self.assertEqual(question.order, 1)


class TestPoll(TracProTest):

    def test_str(self):
        """Smoke test for string representation."""
        poll = factories.Poll(name='hello')
        self.assertEqual(str(poll), 'hello')

    def test_flow_uuid_unique_to_org(self):
        """flow_uuid should be unique for a given Org."""
        org = factories.Org()
        factories.Poll(org=org, flow_uuid='abc')
        with self.assertRaises(IntegrityError):
            factories.Poll(org=org, flow_uuid='abc')

    def test_flow_uuid_can_repeat_between_orgs(self):
        """flow_uuid can be repeated with different Orgs."""
        factories.Poll(org=factories.Org(), flow_uuid='abc')
        factories.Poll(org=factories.Org(), flow_uuid='abc')

    def test_get_flow_definition(self):
        """Flow definition should be retrieved from the API and cached on the poll."""
        definition = factories.TembaFlowDefinition()
        self.mock_temba_client.get_flow_definition.return_value = definition
        poll = factories.Poll()
        self.assertFalse(hasattr(poll, '_flow_definition'))
        for i in range(2):
            # The result of the method should be cached on the poll.
            self.assertEqual(poll.get_flow_definition(), definition)
            self.assertEqual(poll._flow_definition, definition)

            # API call count should not go up.
            self.assertEqual(self.mock_temba_client.get_flow_definition.call_count, 1)


class TestQuestionQueryset(TracProTest):

    def test_active(self):
        """is_active() queryset filter should not return Questions with is_active=False."""
        question = factories.Question(is_active=True)
        factories.Question(is_active=False)
        self.assertEqual(list(models.Question.objects.active()), [question])


class TestQuestionManager(TracProTest):

    def setUp(self):
        super(TestQuestionManager, self).setUp()
        self.mock_temba_client.get_flow_definition.return_value = factories.TembaFlowDefinition()

    def test_from_temba__new(self):
        """Should create a new Question to match the Poll and uuid."""
        poll = factories.Poll()
        ruleset = factories.TembaRuleSet()

        # Should create a new Question object that matches the incoming data.
        question = models.Question.objects.from_temba(poll, ruleset, order=100)
        self.assertEqual(models.Question.objects.count(), 1)
        self.assertEqual(question.ruleset_uuid, ruleset.uuid)
        self.assertEqual(question.poll, poll)
        self.assertEqual(question.rapidpro_name, ruleset.label)
        self.assertEqual(question.question_type, models.Question.TYPE_OPEN)
        self.assertEqual(question.order, 100)

    def test_from_temba__existing(self):
        """Should update an existing Question for the Poll and uuid."""
        poll = factories.Poll()
        question = factories.Question(
            poll=poll, question_type=models.Question.TYPE_OPEN)
        ruleset = factories.TembaRuleSet(
            uuid=question.ruleset_uuid,
            response_type=models.Question.TYPE_MULTIPLE_CHOICE)

        # Should return the existing Question object.
        ret_val = models.Question.objects.from_temba(poll, ruleset, order=100)
        self.assertEqual(ret_val, question)
        self.assertEqual(ret_val.ruleset_uuid, question.ruleset_uuid)
        self.assertEqual(models.Question.objects.count(), 1)

        # Existing Question should be updated to match the incoming data.
        question.refresh_from_db()
        self.assertEqual(question.ruleset_uuid, ruleset.uuid)
        self.assertEqual(question.poll, poll)
        self.assertEqual(question.rapidpro_name, ruleset.label)
        self.assertEqual(question.order, 100)

        # Question type should not be updated.
        self.assertEqual(question.question_type, models.Question.TYPE_OPEN)

    def test_from_temba__another_org(self):
        """Both uuid and Poll must match in order to update existing."""
        poll = factories.Poll()
        other_poll = factories.Poll()
        other_question = factories.Question(poll=other_poll)
        ruleset = factories.TembaRuleSet(uuid=other_question.ruleset_uuid)

        # Should return a Question that is distinct from the existing
        # Question for another poll.
        ret_val = models.Question.objects.from_temba(poll, ruleset, order=100)
        self.assertEqual(models.Question.objects.count(), 2)
        other_question.refresh_from_db()
        self.assertNotEqual(ret_val, other_question)
        self.assertNotEqual(ret_val.poll, other_question.poll)
        self.assertEqual(ret_val.ruleset_uuid, other_question.ruleset_uuid)


class TestQuestion(TracProTest):

    def test_str(self):
        """Smoke test for string representation."""
        question = factories.Question(name='hello')
        self.assertEqual(str(question), 'hello')

    def test_ruleset_uuid_unique_to_poll(self):
        """ruleset_uuid should be unique for a particular Poll."""
        poll = factories.Poll()
        factories.Question(poll=poll, ruleset_uuid='abc')
        with self.assertRaises(IntegrityError):
            factories.Question(poll=poll, ruleset_uuid='abc')

    def test_ruleset_uuid_can_repeat_between_polls(self):
        """ruleset_uuid can be repeated with different Polls."""
        factories.Question(poll=factories.Poll(), ruleset_uuid='abc')
        factories.Question(poll=factories.Poll(), ruleset_uuid='abc')

    def test_categorize(self):
        rules = [
            {
                'category': {'base': 'dogs'},
                'test': {'type': 'between', 'min': 1, 'max': 3}
            },
            {
                'category': {'base': 'cats'},
                'test': {'type': 'numeric'},
            },
        ]
        question = factories.Question(json_rules=json.dumps(rules))
        self.assertEqual(question.categorize(2), 'dogs')
        self.assertEqual(question.categorize(5), 'cats')
        self.assertEqual(question.categorize("foo"), 'Other')

    def test_guess_question_type_numeric(self):
        """Guess NUMERIC if rule types are all numeric."""
        question = factories.Question(json_rules=json.dumps([
            {'test': {'type': 'number'}},
            {'test': {'type': 'number'}},
        ]))
        self.assertEqual(question.guess_question_type(), models.Question.TYPE_NUMERIC)

    def test_guess_question_type_open(self):
        """Guess OPEN if there are no rules."""
        question = factories.Question(json_rules=json.dumps([]))
        self.assertEqual(question.guess_question_type(), models.Question.TYPE_OPEN)

    def test_guess_question_type_multiple_choice(self):
        """Guess MULTIPLE_CHOICE if not all rules are numeric."""
        question = factories.Question(json_rules=json.dumps([
            {'test': {'type': 'number'}},
            {'test': {'type': 'text'}},
        ]))
        self.assertEqual(question.guess_question_type(), models.Question.TYPE_MULTIPLE_CHOICE)


class PollRunTest(TracProDataTest):

    def test_get_or_create_universal(self):
        # 2014-Jan-01 04:30 in org's Afg timezone
        with mock.patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc)
            # no existing pollruns so one is created
            pollrun1 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(
                pollrun1.conducted_on,
                datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc))

        # 2014-Jan-01 23:30 in org's Afg timezone
        with mock.patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 19, 0, 0, 0, pytz.utc)
            # existing pollrun on same day is returned
            pollrun2 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(pollrun1, pollrun2)

        # 2014-Jan-02 00:30 in org's Afg timezone
        with mock.patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc)
            # different day locally so new pollrun
            pollrun3 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertNotEqual(pollrun3, pollrun1)
            self.assertEqual(
                pollrun3.conducted_on,
                datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc))

        # 2014-Jan-02 04:30 in org's Afg timezone
        with mock.patch.object(timezone, 'now') as mock_now:
            mock_now.return_value = datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.utc)
            # same day locally so no new pollrun
            pollrun4 = PollRun.objects.get_or_create_universal(self.poll1)
            self.assertEqual(pollrun3, pollrun4)

    def test_completion(self):
        date1 = datetime.datetime(2014, 1, 1, 7, tzinfo=pytz.UTC)

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


class TestResponse(TracProDataTest):

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


class TestAnswer(TracProDataTest):

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
