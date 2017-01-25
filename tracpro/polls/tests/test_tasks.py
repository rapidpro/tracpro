from __future__ import unicode_literals

import mock

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import models
from ..tasks import sync_questions_categories


class TestPollTask(TracProTest):

    @mock.patch.object(models.Poll, 'get_flow_definition')
    @mock.patch('tracpro.polls.tasks.logger.info')
    def test_sync_questions_categories(self, mock_logger, mock_poll_get_flow):
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
        flow_1 = mock.Mock()
        flow_1.uuid = 'abcdefg123'
        flow_1.name = self.poll_1.name
        ruleset_existing = mock.Mock()
        ruleset_existing.uuid = 'goodquestion'
        ruleset_existing.label = 'good question'
        ruleset_new = mock.Mock()
        ruleset_new.uuid = 'newquestion'
        ruleset_new.label = 'new question'
        flow_1.rulesets = [ruleset_existing, ruleset_new]

        # Mock the call to the API to send back a single flow matching our first poll
        self.mock_temba_client.get_flows.return_value = [flow_1]
        # Mock this call to return an empty rule set so that RapidPro API is not called
        mock_poll_get_flow.return_value.rulesets = []

        # Assert that the 2 questions exist before we sync when one should be deleted
        self.assertEqual(models.Question.objects.count(), 2)

        # Call the task to sync questions...
        sync_questions_categories(self.org, self.data)
        # Two questions exist locally, one is new from the RapidPro API mock (flow_1.rulesets)
        self.assertEqual(models.Question.objects.count(), 2)
        self.assertEqual(models.Question.objects.first().ruleset_uuid, 'goodquestion')
        self.assertEqual(models.Question.objects.last().ruleset_uuid, 'newquestion')
        # Only 1 poll was reflected in the log message as only 1 poll was sent into the form data
        self.assertEqual(mock_logger.call_count, 2)
        self.assertIn("1 Poll(s)", mock_logger.call_args[0][0])
