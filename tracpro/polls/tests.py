from __future__ import absolute_import, unicode_literals

import datetime
import pytz

from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch
from temba.types import Flow, FlowRuleSet, Run, RunValueSet
from tracpro.test import TracProTest
from .models import Poll, Issue, Response


class PollTest(TracProTest):
    @patch('dash.orgs.models.TembaClient.get_flows')
    def test_sync_with_flows(self, mock_get_flows):
        mock_get_flows.return_value = [
            Flow.create(name="Poll #3", uuid='F-003', rulesets=[
                FlowRuleSet.create(uuid='RS-004', label='How old are you'),
                FlowRuleSet.create(uuid='RS-005', label='Where do you live')
            ]),
            Flow.create(name="Poll #4", uuid='F-004', rulesets=[
                FlowRuleSet.create(uuid='RS-006', label='How many goats'),
                FlowRuleSet.create(uuid='RS-007', label='How many sheep')
            ]),
            Flow.create(name="Poll #5", uuid='F-005', rulesets=[
                FlowRuleSet.create(uuid='RS-008', label='What time is it')
            ])
        ]
        Poll.sync_with_flows(self.unicef, ['F-003', 'F-004'])

        self.assertEqual(self.unicef.polls.filter(is_active=True).count(), 2)

        # existing poll that wasn't included should now be inactive
        self.assertFalse(Poll.objects.get(flow_uuid='F-001').is_active)

        poll3 = Poll.objects.get(flow_uuid='F-003')
        self.assertEqual(poll3.name, "Poll #3")
        self.assertEqual(poll3.questions.count(), 2)


class IssueTest(TracProTest):
    def test_get_or_create(self):
        # 2014-Jan-01 04:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc)):
            # no existing issues so one is created
            issue1 = Issue.get_or_create(self.unicef, self.poll1)
            self.assertEqual(issue1.conducted_on, datetime.datetime(2014, 1, 1, 0, 0, 0, 0, pytz.utc))

        # 2014-Jan-01 23:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 19, 0, 0, 0, pytz.utc)):
            # existing issue on same day is returned
            issue2 = Issue.get_or_create(self.unicef, self.poll1)
            self.assertEqual(issue1, issue2)

        # 2014-Jan-02 00:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc)):
            # different day locally so new issue
            issue3 = Issue.get_or_create(self.unicef, self.poll1)
            self.assertNotEqual(issue3, issue1)
            self.assertEqual(issue3.conducted_on, datetime.datetime(2014, 1, 1, 20, 0, 0, 0, pytz.utc))

        # 2014-Jan-02 04:30 in org's Afg timezone
        with patch.object(timezone, 'now', return_value=datetime.datetime(2014, 1, 2, 0, 0, 0, 0, pytz.utc)):
            # same day locally so no new issue
            issue4 = Issue.get_or_create(self.unicef, self.poll1)
            self.assertEqual(issue3, issue4)


class ResponseTest(TracProTest):
    def test_get_or_create(self):
        # a complete run
        run = Run.create(id=1234,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-001',
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

        response = Response.get_or_create(self.unicef, run)
        self.assertEqual(response.contact, self.contact1)
        self.assertEqual(response.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response.updated_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertTrue(response.is_complete)
        self.assertEqual(len(response.answers.all()), 2)
        answers = list(response.answers.order_by('question_id'))
        self.assertEqual(answers[0].question, self.poll1_question1)
        self.assertEqual(answers[0].value, "6.00000000")
        self.assertEqual(answers[0].category, "1 - 50")
        self.assertEqual(answers[0].submitted_on, datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(answers[1].question, self.poll1_question2)
        self.assertEqual(answers[1].value, "4.00000000")
        self.assertEqual(answers[1].category, "1 - 25")
        self.assertEqual(answers[1].submitted_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))

        # an incomplete run
        run = Run.create(id=2345,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-002',
                         values=[RunValueSet.create(category="1 - 50",
                                                    node='RS-001',
                                                    text="6",
                                                    value="6.00000000",
                                                    label="Number of sheep",
                                                    time=datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response = Response.get_or_create(self.unicef, run)
        self.assertEqual(response.contact, self.contact2)
        self.assertEqual(response.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response.updated_on, datetime.datetime(2014, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertFalse(response.is_complete)
        self.assertEqual(len(response.answers.all()), 1)

        # now completed
        run = Run.create(id=2345,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-002',
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

        response = Response.get_or_create(self.unicef, run)
        self.assertEqual(response.contact, self.contact2)
        self.assertEqual(response.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response.updated_on, datetime.datetime(2015, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertTrue(response.is_complete)
        self.assertEqual(len(response.answers.all()), 2)

        # an empty run
        run = Run.create(id=3456,
                         flow='F-001',  # flow UUID for poll #1
                         contact='C-002',
                         values=[],
                         steps=[],  # not used
                         created_on=datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))

        response = Response.get_or_create(self.unicef, run)
        self.assertEqual(response.contact, self.contact2)
        self.assertEqual(response.created_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertEqual(response.updated_on, datetime.datetime(2013, 1, 2, 3, 4, 5, 6, pytz.UTC))
        self.assertFalse(response.is_complete)
        self.assertEqual(len(response.answers.all()), 0)


class PollCRUDLTest(TracProTest):
    def test_list(self):
        url = reverse('polls.poll_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)


class QuestionCRUDLTest(TracProTest):
    def test_filter(self):
        # log in as admin
        self.login(self.admin)

        # view questions for our only poll
        response = self.url_get('unicef', reverse('polls.question_filter', args=[self.poll1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)


class PollTasksTest(TracProTest):
    pass
