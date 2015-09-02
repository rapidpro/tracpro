from __future__ import absolute_import, unicode_literals

from mock import patch

from django.test.utils import override_settings
from django.utils import timezone

from temba.types import Broadcast

from tracpro.msgs.models import (
    Message, COHORT_ALL, COHORT_RESPONDENTS, COHORT_NONRESPONDENTS)
from tracpro.polls.models import (
    PollRun, Response, RESPONSE_COMPLETE, RESPONSE_PARTIAL, RESPONSE_EMPTY)
from tracpro.test.cases import TracProDataTest


class MessageTest(TracProDataTest):

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    @patch('dash.orgs.models.TembaClient.create_broadcast')
    def test_create(self, mock_create_broadcast):
        mock_create_broadcast.return_value = Broadcast.create()
        now = timezone.now()

        # create non-regional pollrun with 3 responses (1 complete, 1 partial, 1 empty)
        pollrun1 = PollRun.objects.create(
            poll=self.poll1, region=None, conducted_on=timezone.now())

        Response.objects.create(
            flow_run_id=123, pollrun=pollrun1, contact=self.contact1,
            created_on=now, updated_on=now, status=RESPONSE_COMPLETE)
        Response.objects.create(
            flow_run_id=234, pollrun=pollrun1, contact=self.contact2,
            created_on=now, updated_on=now, status=RESPONSE_PARTIAL)
        Response.objects.create(
            flow_run_id=345, pollrun=pollrun1, contact=self.contact4,
            created_on=now, updated_on=now, status=RESPONSE_EMPTY)

        msg1 = Message.create(
            self.unicef, self.admin, "Test #1", pollrun1, COHORT_ALL, None)
        self.assertEqual(msg1.org, self.unicef)
        self.assertEqual(msg1.sent_by, self.admin)
        self.assertIsNotNone(msg1.sent_on)
        self.assertEqual(msg1.text, "Test #1")
        self.assertEqual(msg1.pollrun, pollrun1)
        self.assertEqual(msg1.cohort, COHORT_ALL)
        self.assertEqual(msg1.region, None)
        self.assertEqual(list(msg1.recipients.order_by('pk')),
                         [self.contact1, self.contact2, self.contact4])
        self.assertEqual(str(msg1), "Test #1")

        self.assertEqual(msg1.as_json(), dict(id=msg1.pk, recipients=3))

        msg2 = Message.create(
            self.unicef, self.admin, "Test #1", pollrun1, COHORT_RESPONDENTS,
            None)
        self.assertEqual(msg2.cohort, COHORT_RESPONDENTS)
        self.assertEqual(msg2.region, None)
        self.assertEqual(list(msg2.recipients.order_by('pk')), [self.contact1])

        msg3 = Message.create(
            self.unicef, self.admin, "Test #1", pollrun1,
            COHORT_NONRESPONDENTS, None)
        self.assertEqual(msg3.cohort, COHORT_NONRESPONDENTS)
        self.assertEqual(msg3.region, None)
        self.assertEqual(list(msg3.recipients.order_by('pk')),
                         [self.contact2, self.contact4])

        msg4 = Message.create(
            self.unicef, self.admin, "Test #1", pollrun1, COHORT_ALL,
            self.region1)
        self.assertEqual(msg4.cohort, COHORT_ALL)
        self.assertEqual(msg4.region, self.region1)
        self.assertEqual(list(msg4.recipients.order_by('pk')),
                         [self.contact1, self.contact2])
