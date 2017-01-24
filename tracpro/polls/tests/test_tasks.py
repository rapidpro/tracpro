from __future__ import unicode_literals

import mock

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import models
from ..tasks import sync_questions_categories


class TestPollTask(TracProTest):

    @mock.patch.object(models.Question.objects, 'from_temba')
    def test_sync_questions_categories(self, mock_question_from_temba):
        self.org = factories.Org()
        self.poll_1 = factories.Poll(org=self.org)
        self.poll_2 = factories.Poll(org=self.org)
        # Create 2 questions locally:
        # one that is on RapidPro
        # and one that should be removed because it won't be on RapidPro
        self.question_1 = factories.Question(poll=self.poll_1, ruleset_uuid='goodquestion')
        self.question_2 = factories.Question(poll=self.poll_1, ruleset_uuid='oldquestion')

        # Data to pass to form for testing. Only select one poll
        self.data = [self.poll_1]
        # Patch the call to the API
        flow_1 = mock.Mock()
        flow_1.uuid = 'abcdefg123'
        flow_1.name = self.poll_1.name
        ruleset = mock.Mock()
        ruleset.uuid = 'goodquestion'
        flow_1.rulesets = [ruleset]
        self.mock_temba_client.get_flows.return_value = [flow_1]

        # Assert that the 2 questions exist before we sync when one should be deleted
        self.assertEqual(models.Question.objects.all().count(), 2)
        with mock.patch('tracpro.polls.tasks.logger.info') as mock_logger:
            sync_questions_categories(self.org, self.data)
            self.assertEqual(models.Question.objects.all().count(), 1)  # only one question should remain
            self.assertEqual(models.Question.objects.first().ruleset_uuid, 'goodquestion')
            # Only 1 poll was reflected in the log message as only 1 poll was sent into the form data
            self.assertEqual(mock_logger.call_count, 2)
            self.assertIn("1 Poll(s)", mock_logger.call_args[0][0])
