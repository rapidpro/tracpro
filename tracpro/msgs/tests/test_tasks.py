from __future__ import absolute_import, unicode_literals

from tracpro.msgs.models import Message, STATUS_SENT, STATUS_FAILED
from tracpro.msgs.tasks import send_message
from tracpro.test import factories
from tracpro.test.cases import TracProTest


class MessageBroadcastTest(TracProTest):
    def setUp(self):
        super(MessageBroadcastTest, self).setUp()
        sender = factories.User()
        org = factories.Org()
        self.message = Message.objects.create(org=org, sent_by=sender)

    def test_two_recipients(self):
        contacts = [factories.Contact() for i in range(2)]
        self.message.recipients.add(*contacts)
        send_message(self.message.id)
        self.message.refresh_from_db()
        self.assertEqual(STATUS_SENT, self.message.status)
        # only one call
        self.assertEqual(1, self.mock_temba_client.create_broadcast.call_count)

    def test_102_recipients(self):
        # We loop if there are more than 100
        contacts = [factories.Contact() for i in range(102)]
        self.message.recipients.add(*contacts)
        send_message(self.message.id)
        self.message.refresh_from_db()
        self.assertEqual(STATUS_SENT, self.message.status)
        # Two calls
        self.assertEqual(2, self.mock_temba_client.create_broadcast.call_count)

    def test_failure(self):
        contacts = [factories.Contact() for i in range(1)]
        self.message.recipients.add(*contacts)
        self.mock_temba_client.create_broadcast.side_effect = TypeError
        send_message(self.message.id)
        self.message.refresh_from_db()
        self.assertEqual(STATUS_FAILED, self.message.status)
