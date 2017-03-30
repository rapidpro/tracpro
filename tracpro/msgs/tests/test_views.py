from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.utils import timezone

from tracpro.msgs.models import Message, COHORT_ALL, InboxMessage
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest


class MessageCRUDLTest(TracProDataTest):
    def test_list(self):
        url = reverse('msgs.message_list')

        # create a non-regional pollrun
        pollrun1 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=timezone.now())

        # send 1 message to all regions and 2 more to specific regions
        msg1 = Message.create(
            self.unicef, self.admin, "Test to all", pollrun1, COHORT_ALL,
            None)
        msg2 = Message.create(
            self.unicef, self.admin, "Test to panel #1", pollrun1,
            COHORT_ALL, self.region1)
        msg3 = Message.create(
            self.unicef, self.admin, "Test to panel #2", pollrun1,
            COHORT_ALL, self.region2)

        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']), [msg3, msg2, msg1])

        self.switch_region(self.region1)

        # should still include message sent to all regions
        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']), [msg2, msg1])


class InboxMessageCRUDLTest(TracProDataTest):
    def setUp(self):
        super(InboxMessageCRUDLTest, self).setUp()
        self.login(self.admin)

        self.inboxmsg1 = InboxMessage.objects.create(
            org=self.unicef,
            rapidpro_message_id=1234,
            contact=self.contact1,
            text="Test message to contact1",
            archived=False,
            direction="O",
            created_on=timezone.now(),
        )

        self.inboxmsg2 = InboxMessage.objects.create(
            org=self.unicef,
            rapidpro_message_id=4567,
            contact=self.contact1,
            text="A more recent test message to contact1",
            archived=False,
            direction="O",
            created_on=timezone.now(),
        )

        self.inboxmsg3 = InboxMessage.objects.create(
            org=self.unicef,
            rapidpro_message_id=6789,
            contact=self.contact2,
            text="A message from contact2",
            archived=False,
            direction="I",
            created_on=timezone.now(),
        )

    def test_list(self):
        url = reverse('msgs.inboxmessage_list')

        # Only the most recent message related per contact should display
        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']),
                         [self.inboxmsg2, self.inboxmsg3])

    def test_conversation(self):
        url = reverse('msgs.inboxmessage_conversation', args=[self.contact1.pk])

        # All messages should display for this contact
        response = self.url_get('unicef', url)
        self.assertEqual(list(response.context['object_list']),
                         [self.inboxmsg2, self.inboxmsg1])
