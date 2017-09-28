from __future__ import unicode_literals

import mock

from tracpro.polls.models import PollRun
from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import models
from ..tasks import sync_questions_categories, pollrun_start


class TestPollTask(TracProTest):

    @mock.patch('tracpro.polls.tasks.logger.info')
    def test_sync_questions_categories(self, mock_logger):
        self.org = factories.Org()
        self.poll_1 = factories.Poll(org=self.org, name='Poll 1')
        self.poll_2 = factories.Poll(org=self.org, name='Poll 2')
        # Create 2 questions locally:
        # one that is on RapidPro
        # and one that should be removed because it won't be on RapidPro
        self.question_1 = factories.Question(
            poll=self.poll_1, ruleset_uuid='goodquestion', question_type=models.Question.TYPE_MULTIPLE_CHOICE)
        self.question_2 = factories.Question(
            poll=self.poll_1, ruleset_uuid='oldquestion', question_type=models.Question.TYPE_MULTIPLE_CHOICE)

        # Data to pass to form for testing. Only select one poll
        self.data = [self.poll_1]
        # Patch the call to the API
        ruleset_existing = {
            'uuid': 'goodquestion',
            'label': 'good question',
            'rules': [],
        }
        ruleset_new = {
            'uuid': 'newquestion',
            'label': 'new question',
            'rules': [],
        }
        # An item in the .flows part of the get_definitions response
        flow_1 = {
            'metadata': {
                'uuid': self.poll_1.flow_uuid,
                'name': self.poll_1.name,
            },
            'rule_sets': [
                ruleset_existing,
                ruleset_new,
            ]
        }
        # A flow item we didn't ask for and should ignore
        flow_2 = {
            'metadata': {
                'uuid': self.poll_2.flow_uuid,
                'name': self.poll_2.name,
            },
            'rule_sets': []
        }

        # Mock the call to the API to send back an Export object containing a
        # single flow matching our first poll
        export_object = factories.TembaExport(flows=[flow_1, flow_2])
        self.mock_temba_client.get_definitions.return_value = export_object

        # Assert that the 2 questions exist before we sync when one should be deleted
        self.assertEqual(models.Question.objects.count(), 2)

        # Call the task to sync questions...
        sync_questions_categories(self.org, self.data)
        # Two questions exist locally, one is new from the RapidPro API mock (flow_1.rulesets)
        self.assertEqual(models.Question.objects.count(), 2)
        self.assertEqual(models.Question.objects.first().ruleset_uuid, 'goodquestion')
        self.assertEqual(models.Question.objects.last().ruleset_uuid, 'newquestion')
        # Only 1 poll was reflected in the log message as only 1 poll was sent into the form data
        self.assertEqual(mock_logger.call_count, 3)
        self.assertIn("1 Poll(s)", mock_logger.call_args[0][0])

    def test_start_flow_runs_one_contact(self):
        self.org = factories.Org()
        pollrun = factories.PollRun(
            poll__org=self.org,
            pollrun_type=PollRun.TYPE_REGIONAL,
        )
        contact = factories.Contact(org=self.org, region=pollrun.region)
        self.mock_temba_client.create_flow_start.return_value = []
        pollrun_start(pollrun.id)
        # Calls to create_flow_start?
        call_args = self.mock_temba_client.create_flow_start.call_args_list
        num_calls = len(call_args)
        self.assertEqual(1, num_calls)
        self.assertEqual(
            call_args[0],
            mock.call(
                contacts=[contact.uuid],
                flow=pollrun.poll.flow_uuid,
                restart_participants=True,
                urns=None
            )
        )

    def test_start_flow_runs_150_contacts(self):
        self.org = factories.Org()
        pollrun = factories.PollRun(
            poll__org=self.org,
            pollrun_type=PollRun.TYPE_REGIONAL,
        )
        contacts = [factories.Contact(org=self.org, region=pollrun.region) for _ in range(150)]

        self.mock_temba_client.create_flow_start.return_value = []
        pollrun_start(pollrun.id)

        # What calls were made?
        call_args = self.mock_temba_client.create_flow_start.call_args_list
        num_calls = len(call_args)
        self.assertEqual(2, num_calls)
        self.assertEqual(100, len(call_args[0][1]['contacts']))
        self.assertEqual(50, len(call_args[1][1]['contacts']))

        # We don't know what order the contacts will be used in.
        # First check the other args.

        self.assertEqual(
            call_args[0],
            mock.call(
                contacts=mock.ANY,
                flow=pollrun.poll.flow_uuid,
                restart_participants=True,
                urns=None
            )
        )
        self.assertEqual(
            call_args[1],
            mock.call(
                contacts=mock.ANY,
                flow=pollrun.poll.flow_uuid,
                restart_participants=True,
                urns=None
            )
        )

        # now make sure all the right contacts were passed
        contacts_passed = set(call_args[0][1]['contacts']) | set(call_args[1][1]['contacts'])
        self.assertEqual(150, len(contacts_passed))
        self.assertEqual(contacts_passed, set([c.uuid for c in contacts]))
