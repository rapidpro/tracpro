from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Broadcast
from tracpro.msgs.models import Message, COHORT_ALL, COHORT_RESPONDENTS, COHORT_NONRESPONDENTS
from tracpro.polls.models import Issue, Response, RESPONSE_COMPLETE, RESPONSE_PARTIAL, RESPONSE_EMPTY
from tracpro.test import TracProTest


class MessageTest(TracProTest):
    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.create_broadcast')
    def test_create(self, mock_create_broadcast):
        mock_create_broadcast.return_value = Broadcast.create()
        now = timezone.now()

        # create non-regional issue with 3 responses (1 complete, 1 partial, 1 empty)
        issue1 = Issue.objects.create(poll=self.poll1, region=None, conducted_on=timezone.now())

        Response.objects.create(flow_run_id=123, issue=issue1, contact=self.contact1,
                                created_on=now, updated_on=now, status=RESPONSE_COMPLETE)
        Response.objects.create(flow_run_id=234, issue=issue1, contact=self.contact2,
                                created_on=now, updated_on=now, status=RESPONSE_PARTIAL)
        Response.objects.create(flow_run_id=345, issue=issue1, contact=self.contact4,
                                created_on=now, updated_on=now, status=RESPONSE_EMPTY)

        msg1 = Message.create(self.unicef, self.admin, "Test #1", issue1, COHORT_ALL, None)
        self.assertEqual(msg1.org, self.unicef)
        self.assertEqual(msg1.sent_by, self.admin)
        self.assertIsNotNone(msg1.sent_on)
        self.assertEqual(msg1.text, "Test #1")
        self.assertEqual(msg1.issue, issue1)
        self.assertEqual(msg1.cohort, COHORT_ALL)
        self.assertEqual(msg1.region, None)
        self.assertEqual(list(msg1.recipients.order_by('pk')), [self.contact1, self.contact2, self.contact4])
        self.assertEqual(unicode(msg1), "Test #1")

        self.assertEqual(msg1.as_json(), dict(id=msg1.pk, recipients=3))

        msg2 = Message.create(self.unicef, self.admin, "Test #1", issue1, COHORT_RESPONDENTS, None)
        self.assertEqual(msg2.cohort, COHORT_RESPONDENTS)
        self.assertEqual(msg2.region, None)
        self.assertEqual(list(msg2.recipients.order_by('pk')), [self.contact1])

        msg3 = Message.create(self.unicef, self.admin, "Test #1", issue1, COHORT_NONRESPONDENTS, None)
        self.assertEqual(msg3.cohort, COHORT_NONRESPONDENTS)
        self.assertEqual(msg3.region, None)
        self.assertEqual(list(msg3.recipients.order_by('pk')), [self.contact2, self.contact4])

        msg4 = Message.create(self.unicef, self.admin, "Test #1", issue1, COHORT_ALL, self.region1)
        self.assertEqual(msg4.cohort, COHORT_ALL)
        self.assertEqual(msg4.region, self.region1)
        self.assertEqual(list(msg4.recipients.order_by('pk')), [self.contact1, self.contact2])


class MessageCRUDLTest(TracProTest):
    def test_list(self):
        url = reverse('msgs.message_list')

        # create a non-regional issue
        issue1 = Issue.objects.create(poll=self.poll1, region=None, conducted_on=timezone.now())

        # send 1 message to all regions and 2 more to specific regions
        msg1 = Message.create(self.unicef, self.admin, "Test to all", issue1, COHORT_ALL, None)
        msg2 = Message.create(self.unicef, self.admin, "Test to region #1", issue1, COHORT_ALL, self.region1)
        msg3 = Message.create(self.unicef, self.admin, "Test to region #2", issue1, COHORT_ALL, self.region2)

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']), [msg3, msg2, msg1])

        self.switch_region(self.region1)

        # should still include message sent to all regions
        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']), [msg2, msg1])
