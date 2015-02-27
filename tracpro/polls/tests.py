# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime
import pytz

from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch
from temba.types import Flow, FlowRuleSet, Run, RunValueSet
from tracpro.test import TracProTest
from .models import Poll, Issue, Response, Answer, RESPONSE_EMPTY, RESPONSE_PARTIAL, RESPONSE_COMPLETE
from .models import extract_words


class PollTest(TracProTest):
    @patch('dash.orgs.models.TembaClient.get_flows')
    def test_sync_with_flows(self, mock_get_flows):
        mock_get_flows.return_value = [
            Flow.create(name="Poll #3", uuid='F-003', rulesets=[
                FlowRuleSet.create(uuid='RS-004', label='How old are you', response_type='C'),
                FlowRuleSet.create(uuid='RS-005', label='Where do you live', response_type='O')
            ]),
            Flow.create(name="Poll #4", uuid='F-004', rulesets=[
                FlowRuleSet.create(uuid='RS-006', label='How many goats', response_type='N'),
                FlowRuleSet.create(uuid='RS-007', label='How many sheep', response_type='N')
            ]),
            Flow.create(name="Poll #5", uuid='F-005', rulesets=[
                FlowRuleSet.create(uuid='RS-008', label='What time is it', response_type='O')
            ])
        ]
        Poll.sync_with_flows(self.unicef, ['F-003', 'F-004'])

        self.assertEqual(self.unicef.polls.filter(is_active=True).count(), 2)

        # existing poll that wasn't included should now be inactive
        self.assertFalse(Poll.objects.get(flow_uuid='F-001').is_active)

        poll3 = Poll.objects.get(flow_uuid='F-003')
        self.assertEqual(poll3.name, "Poll #3")
        self.assertEqual(poll3.questions.count(), 2)
        self.assertEqual(unicode(poll3), "Poll #3")

        # switch back to flow #1
        mock_get_flows.return_value = [
            Flow.create(name="Poll #1", uuid='F-001', rulesets=[
                FlowRuleSet.create(uuid='RS-001', label='Number of sheep', response_type='N'),
                FlowRuleSet.create(uuid='RS-002', label='Number of goats', response_type='N')
            ])
        ]

        Poll.sync_with_flows(self.unicef, ['F-001'])

        # existing poll that was inactive should now be active
        self.assertTrue(Poll.objects.get(flow_uuid='F-001').is_active)

    def test_get_update_required(self):
        # no issues means no responses to update
        self.assertEqual(Response.get_update_required(self.unicef).count(), 0)

        # create issue but no responses yet
        issue1 = Issue.get_or_create_non_regional(self.unicef, self.poll1, for_date=self.datetime(2014, 1, 1))

        self.assertEqual(Response.get_update_required(self.unicef).count(), 0)

        # add an empty, a partial and a complete response
        response1 = Response.objects.create(flow_run_id=123, issue=issue1, contact=self.contact1,
                                            created_on=timezone.now(), updated_on=timezone.now(), status=RESPONSE_EMPTY)
        response2 = Response.objects.create(flow_run_id=234, issue=issue1, contact=self.contact2,
                                            created_on=timezone.now(), updated_on=timezone.now(), status=RESPONSE_PARTIAL)
        Response.objects.create(flow_run_id=345, issue=issue1, contact=self.contact3,
                                created_on=timezone.now(), updated_on=timezone.now(), status=RESPONSE_COMPLETE)

        self.assertEqual(list(Response.get_update_required(self.unicef).order_by('pk')), [response1, response2])

        # create newer issue with an incomplete response
        issue2 = Issue.get_or_create_non_regional(self.unicef, self.poll1, for_date=self.datetime(2014, 1, 2))
        response3 = Response.objects.create(flow_run_id=456, issue=issue2, contact=self.contact1,
                                            created_on=timezone.now(), updated_on=timezone.now(), status=RESPONSE_EMPTY)

        # shouldn't include any responses from older issue
        self.assertEqual(list(Response.get_update_required(self.unicef)), [response3])

    def test_get_questions(self):
        self.assertEqual(list(self.poll1.get_questions()), [self.poll1_question1, self.poll1_question2])
        self.assertEqual(list(self.poll2.get_questions()), [self.poll2_question1])


class IssueTest(TracProTest):
    def test_get_or_create_non_regional(self):
        # 2014-Jan-01 04:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc)):
            # no existing issues so one is created
            issue1 = Issue.get_or_create_non_regional(self.unicef, self.poll1)
            self.assertEqual(issue1.conducted_on, datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc))

        # 2014-Jan-01 23:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 19, 0, 0, 0, pytz.utc)):
            # existing issue on same day is returned
            issue2 = Issue.get_or_create_non_regional(self.unicef, self.poll1)
            self.assertEqual(issue1, issue2)

        # 2014-Jan-02 00:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc)):
            # different day locally so new issue
            issue3 = Issue.get_or_create_non_regional(self.unicef, self.poll1)
            self.assertNotEqual(issue3, issue1)
            self.assertEqual(issue3.conducted_on, datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc))

        # 2014-Jan-02 04:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.utc)):
            # same day locally so no new issue
            issue4 = Issue.get_or_create_non_regional(self.unicef, self.poll1)
            self.assertEqual(issue3, issue4)

    def test_completion(self):
        date1 = self.datetime(2014, 1, 1, 7, 0)

        # issue with no responses (complete or incomplete) has null completion
        issue = Issue.objects.create(poll=self.poll1, conducted_on=date1)

        # add a incomplete response from contact in region #1
        response1 = Response.objects.create(flow_run_id=123, issue=issue, contact=self.contact1,
                                            created_on=date1, updated_on=date1, status=RESPONSE_EMPTY)

        self.assertEqual(list(issue.get_responses()), [response1])
        self.assertEqual(issue.get_response_counts(),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 0})

        self.assertEqual(list(issue.get_responses(self.region1)), [response1])
        self.assertEqual(issue.get_response_counts(self.region1),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 0})

        self.assertEqual(list(issue.get_responses(self.region2)), [])
        self.assertEqual(issue.get_response_counts(self.region2),
                         {RESPONSE_EMPTY: 0, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 0})

        # add a complete response from another contact in region #1
        response2 = Response.objects.create(flow_run_id=234, issue=issue, contact=self.contact2,
                                            created_on=date1, updated_on=date1, status=RESPONSE_COMPLETE)

        self.assertEqual(list(issue.get_responses().order_by('pk')), [response1, response2])
        self.assertEqual(issue.get_response_counts(),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 1})

        self.assertEqual(list(issue.get_responses(self.region1).order_by('pk')), [response1, response2])
        self.assertEqual(issue.get_response_counts(self.region1),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 1})

        self.assertEqual(list(issue.get_responses(self.region2)), [])
        self.assertEqual(issue.get_response_counts(self.region2),
                         {RESPONSE_EMPTY: 0, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 0})

        # add a complete response from contact in different region
        response3 = Response.objects.create(flow_run_id=345, issue=issue, contact=self.contact4,
                                            created_on=date1, updated_on=date1, status=RESPONSE_COMPLETE)

        self.assertEqual(list(issue.get_responses().order_by('pk')), [response1, response2, response3])
        self.assertEqual(issue.get_response_counts(),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 2})

        self.assertEqual(list(issue.get_responses(self.region1).order_by('pk')), [response1, response2])
        self.assertEqual(issue.get_response_counts(self.region1),
                         {RESPONSE_EMPTY: 1, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 1})

        self.assertEqual(list(issue.get_responses(self.region2)), [response3])
        self.assertEqual(issue.get_response_counts(self.region2),
                         {RESPONSE_EMPTY: 0, RESPONSE_PARTIAL: 0, RESPONSE_COMPLETE: 1})

    def test_is_last_for_region(self):
        issue1 = Issue.objects.create(poll=self.poll1, region=self.region1, conducted_on=timezone.now())
        issue2 = Issue.objects.create(poll=self.poll1, region=None, conducted_on=timezone.now())
        issue3 = Issue.objects.create(poll=self.poll1, region=self.region2, conducted_on=timezone.now())

        self.assertFalse(issue1.is_last_for_region(self.region1))  # issue #2 covers region #1 and is newer
        self.assertFalse(issue1.is_last_for_region(self.region2))  # issue #1 didn't cover region #2
        self.assertTrue(issue2.is_last_for_region(self.region1))
        self.assertFalse(issue2.is_last_for_region(self.region2))  # issue #3 covers region #2 and is newer
        self.assertTrue(issue3.is_last_for_region(self.region2))

    def test_answer_aggregation(self):
        self.contact5.language = 'ara'
        self.contact5.save()

        issue = Issue.objects.create(poll=self.poll1, region=None, conducted_on=timezone.now())

        response1 = Response.create_empty(self.unicef, issue,
                                          Run.create(id=123, contact='C-001', created_on=timezone.now()))
        Answer.create(response1, self.poll1_question1, "4.00000", "1 - 5", timezone.now())
        Answer.create(response1, self.poll1_question2, "It's very rainy", "All Responses", timezone.now())

        response2 = Response.create_empty(self.unicef, issue,
                                          Run.create(id=234, contact='C-002', created_on=timezone.now()))
        Answer.create(response2, self.poll1_question1, "3.00000", "1 - 5", timezone.now())
        Answer.create(response2, self.poll1_question2, "rainy and rainy", "All Responses", timezone.now())

        response3 = Response.create_empty(self.unicef, issue,
                                          Run.create(id=345, contact='C-004', created_on=timezone.now()))
        Answer.create(response3, self.poll1_question1, "8.00000", "6 - 10", timezone.now())
        Answer.create(response3, self.poll1_question2, "Sunny sunny", "All Responses", timezone.now())

        response4 = Response.create_empty(self.unicef, issue,
                                          Run.create(id=456, contact='C-005', created_on=timezone.now()))
        Answer.create(response4, self.poll1_question2, "مطر", "All Responses", timezone.now())

        # category counts for question #1
        self.assertEqual(issue.get_answer_category_counts(self.poll1_question1), [("1 - 5", 2), ("6 - 10", 1)])
        self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region1), [("1 - 5", 2)])
        self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region2), [("6 - 10", 1)])
        self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region3), [])

        # and from cache... (lists rather than tuples due to JSON serialization)
        with self.assertNumQueries(0):
            self.assertEqual(issue.get_answer_category_counts(self.poll1_question1), [["1 - 5", 2], ["6 - 10", 1]])
            self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region1), [["1 - 5", 2]])
            self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region2), [["6 - 10", 1]])
            self.assertEqual(issue.get_answer_category_counts(self.poll1_question1, self.region3), [])

        # auto-range category counts for question #1
        self.assertEqual(issue.get_answer_auto_range_counts(self.poll1_question1),
                         [(u'1 - 2', 0), (u'3 - 4', 2), (u'5 - 6', 0), (u'7 - 8', 1), (u'9 - 10', 0)])
        self.assertEqual(issue.get_answer_auto_range_counts(self.poll1_question1, self.region1),
                         [(u'2', 0), (u'3', 1), (u'4', 1), (u'5', 0), (u'6', 0)])
        self.assertEqual(issue.get_answer_auto_range_counts(self.poll1_question1, self.region2),
                         [(u'6', 0), (u'7', 0), (u'8', 1), (u'9', 0), (u'10', 0)])
        self.assertEqual(issue.get_answer_auto_range_counts(self.poll1_question1, self.region3), [])

        # numeric averages for question #1
        self.assertEqual(issue.get_answer_numeric_average(self.poll1_question1), 5.0)
        self.assertEqual(issue.get_answer_numeric_average(self.poll1_question1, self.region1), 3.5)
        self.assertEqual(issue.get_answer_numeric_average(self.poll1_question1, self.region2), 8.0)
        self.assertEqual(issue.get_answer_numeric_average(self.poll1_question1, self.region3), 0.0)

        # word counts for question #2
        self.assertEqual(issue.get_answer_word_counts(self.poll1_question2),
                         [("rainy", 3), ("sunny", 2), ('مطر', 1)])
        self.assertEqual(issue.get_answer_word_counts(self.poll1_question2, self.region1),
                         [("rainy", 3)])
        self.assertEqual(issue.get_answer_word_counts(self.poll1_question2, self.region2),
                         [("sunny", 2)])
        self.assertEqual(issue.get_answer_word_counts(self.poll1_question2, self.region3),
                         [('مطر', 1)])


class ResponseTest(TracProTest):
    def test_from_run(self):
        # a complete run
        run = Run.create(id=1234,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-001',
                         completed=True,
                         values=[RunValueSet.create(category="1 - 50",
                                                    node='RS-001',
                                                    text="6",
                                                    value="6.00000000",
                                                    label="Number of sheep",
                                                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC)),
                                 RunValueSet.create(category="1 - 25",
                                                    node='RS-002',
                                                    text="4",
                                                    value="4.00000000",
                                                    label="Number of goats",
                                                    time=datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response1 = Response.from_run(self.unicef, run)
        self.assertEqual(response1.contact, self.contact1)
        self.assertEqual(response1.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response1.updated_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response1.status, RESPONSE_COMPLETE)
        self.assertEqual(len(response1.answers.all()), 2)
        answers = list(response1.answers.order_by('question_id'))
        self.assertEqual(answers[0].question, self.poll1_question1)
        self.assertEqual(answers[0].value, "6.00000000")
        self.assertEqual(answers[0].category, "1 - 50")
        self.assertEqual(answers[0].submitted_on, datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(answers[1].question, self.poll1_question2)
        self.assertEqual(answers[1].value, "4.00000000")
        self.assertEqual(answers[1].category, "1 - 25")
        self.assertEqual(answers[1].submitted_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))

        # an partially complete run
        run = Run.create(id=2345,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-002',
                         completed=False,
                         values=[RunValueSet.create(category="1 - 50",
                                                    node='RS-001',
                                                    text="6",
                                                    value="6.00000000",
                                                    label="Number of sheep",
                                                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response2 = Response.from_run(self.unicef, run)
        self.assertEqual(response2.contact, self.contact2)
        self.assertEqual(response2.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response2.updated_on, datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response2.status, RESPONSE_PARTIAL)
        self.assertEqual(len(response2.answers.all()), 1)

        # now completed
        run = Run.create(id=2345,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-002',
                         completed=True,
                         values=[RunValueSet.create(category="1 - 50",
                                                    node='RS-001',
                                                    text="6",
                                                    value="6.00000000",
                                                    label="Number of sheep",
                                                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC)),
                                 RunValueSet.create(category="1 - 25",
                                                    node='RS-002',
                                                    text="4",
                                                    value="4.00000000",
                                                    label="Number of goats",
                                                    time=datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response3 = Response.from_run(self.unicef, run)
        self.assertEqual(response3.contact, self.contact2)
        self.assertEqual(response3.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response3.updated_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response3.status, RESPONSE_COMPLETE)
        self.assertEqual(len(response3.answers.all()), 2)

        # an empty run
        run = Run.create(id=3456,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-003',
                         completed=False,
                         values=[],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response4 = Response.from_run(self.unicef, run)
        self.assertEqual(response4.contact, self.contact3)
        self.assertEqual(response4.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response4.updated_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response4.status, RESPONSE_EMPTY)
        self.assertEqual(len(response4.answers.all()), 0)

        # new run for same contact should de-activate old response
        run = Run.create(id=4567,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-003',
                         completed=False,
                         values=[],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 0, 0, 0, pytz.UTC))

        response5 = Response.from_run(self.unicef, run)
        self.assertFalse(Response.objects.get(pk=response4.pk).is_active)
        self.assertEqual(response5.contact, self.contact3)

        # same run if we call again
        self.assertEqual(Response.from_run(self.unicef, run), response5)


class AnswerTest(TracProTest):
    def test_create(self):
        issue = Issue.objects.create(poll=self.poll1, region=None, conducted_on=timezone.now())
        response = Response.create_empty(self.unicef, issue,
                                         Run.create(id=123, contact='C-001', created_on=timezone.now()))

        answer1 = Answer.create(response, self.poll1_question1, "4.00000", "1 - 5", timezone.now())
        self.assertEqual(answer1.response, response)
        self.assertEqual(answer1.question, self.poll1_question1)
        self.assertEqual(answer1.category, "1 - 5")
        self.assertEqual(answer1.value, "4.00000")

        answer2 = Answer.create(response, self.poll1_question1, "rain", dict(base="Rain", rwa="Imvura"), timezone.now())
        self.assertEqual(answer2.category, "Rain")

        answer3 = Answer.create(response, self.poll1_question1, "rain", dict(eng="Yes"), timezone.now())
        self.assertEqual(answer3.category, "Yes")

    def test_auto_range_counts(self):
        self.assertEqual(Answer.auto_range_counts([], 5), {})
        self.assertEqual(Answer.auto_range_counts([Answer(value=1, category=None)], 5), {})
        self.assertEqual(Answer.auto_range_counts([Answer(value=1, category="1 - 100")], 5),
                         {'0': 0, '1': 1, '2': 0, '3': 0, '4': 0})
        self.assertEqual(Answer.auto_range_counts([Answer(value=1, category="1 - 100"),
                                                   Answer(value=2, category="1 - 100"),
                                                   Answer(value=2, category="1 - 100"),
                                                   Answer(value=3, category="1 - 100")], 5),
                         {'0': 0, '1': 1, '2': 2, '3': 1, '4': 0})
        self.assertEqual(Answer.auto_range_counts([Answer(value=1, category="1 - 100"),
                                                   Answer(value=2, category="1 - 100"),
                                                   Answer(value=6, category="1 - 100"),
                                                   Answer(value=6, category="1 - 100"),
                                                   Answer(value=13, category="1 - 100")], 5),
                         {'0 - 2': 2, '3 - 5': 0, '6 - 8': 2, '9 - 11': 0, '12 - 14': 1})

    def test_numeric_average(self):
        self.assertEqual(Answer.numeric_average([]), 0)
        self.assertEqual(Answer.numeric_average([Answer(value=1, category=None)]), 0)
        self.assertEqual(Answer.numeric_average([Answer(value=1, category="1 - 100"),
                                                 Answer(value=2, category="1 - 100")]), 1.5)


class PollCRUDLTest(TracProTest):
    def test_list(self):
        url = reverse('polls.poll_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class ResponseCRUDLTest(TracProTest):
    def setUp(self):
        super(ResponseCRUDLTest, self).setUp()
        date1 = self.datetime(2014, 1, 1, 7, 0)
        date2 = self.datetime(2014, 1, 1, 8, 0)
        date3 = self.datetime(2014, 1, 2, 7, 0)

        # create non-regional issue with 3 responses (1 complete, 1 partial, 1 empty)
        self.issue1 = Issue.objects.create(poll=self.poll1, region=None, conducted_on=date1)

        self.issue1_r1 = Response.objects.create(flow_run_id=123, issue=self.issue1, contact=self.contact1,
                                                 created_on=date1, updated_on=date1, status=RESPONSE_COMPLETE)
        Answer.create(self.issue1_r1, self.poll1_question1, "5.0000", "1 - 10", date1)
        Answer.create(self.issue1_r1, self.poll1_question2, "Sunny", "All Responses", date1)

        self.issue1_r2 = Response.objects.create(flow_run_id=234, issue=self.issue1, contact=self.contact2,
                                                 created_on=date2, updated_on=date2, status=RESPONSE_PARTIAL)
        Answer.create(self.issue1_r2, self.poll1_question1, "6.0000", "1 - 10", date2)

        self.issue1_r3 = Response.objects.create(flow_run_id=345, issue=self.issue1, contact=self.contact4,
                                                 created_on=date3, updated_on=date3, status=RESPONSE_EMPTY)

        # create regional issue with 1 incomplete response
        self.issue2 = Issue.objects.create(poll=self.poll1, region=self.region1, conducted_on=date3)
        self.issue2_r1 = Response.objects.create(flow_run_id=456, issue=self.issue2, contact=self.contact1,
                                                 created_on=date3, updated_on=date3, status=RESPONSE_PARTIAL)

    def test_by_issue(self):
        # log in as admin
        self.login(self.admin)

        # view responses for issue #1
        response = self.url_get('unicef', reverse('polls.response_by_issue', args=[self.issue1.pk]))
        self.assertContains(response, "Number of sheep", status_code=200)
        self.assertContains(response, "How is the weather?")

        responses = list(response.context['object_list'])
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses, [self.issue1_r2, self.issue1_r1])  # newest non-empty first

        # can't restart from "All Regions" view of responses
        self.assertFalse(response.context['can_restart'])

        self.switch_region(self.region1)

        # can't restart as there is a later issue of the same poll in region #1
        response = self.url_get('unicef', reverse('polls.response_by_issue', args=[self.issue1.pk]))
        self.assertFalse(response.context['can_restart'])

        self.switch_region(self.region2)

        # can restart as this is the latest issue of this poll in region #2
        response = self.url_get('unicef', reverse('polls.response_by_issue', args=[self.issue1.pk]))
        self.assertTrue(response.context['can_restart'])

    def test_by_contact(self):
        # log in as admin
        self.login(self.admin)

        # view responses for contact #1
        response = self.url_get('unicef', reverse('polls.response_by_contact', args=[self.contact1.pk]))

        responses = list(response.context['object_list'])
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses, [self.issue2_r1, self.issue1_r1])  # newest non-empty first


class PollFuncsTest(TracProTest):
    def test_extract_words(self):
        self.assertEqual(extract_words("I think it's good", "eng"), ['think', 'good'])  # I and it's are stop words
        self.assertEqual(extract_words("I think it's good", "kin"), ['think', "it's", 'good'])  # no stop words for kin
        self.assertEqual(extract_words("قلم رصاص", "ara"), ['قلم', 'رصاص'])
