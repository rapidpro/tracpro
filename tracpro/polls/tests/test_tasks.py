from __future__ import unicode_literals

import mock

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import models
from ..tasks import sync_questions_categories


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
