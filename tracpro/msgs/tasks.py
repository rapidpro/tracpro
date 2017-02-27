from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta

from django.utils import timezone

from celery.utils.log import get_task_logger
from djcelery_transactions import task

from tracpro.client import get_client
from tracpro.orgs_ext.tasks import OrgTask


logger = get_task_logger(__name__)


@task
def send_message(message_id):
    from .models import Message, STATUS_SENT, STATUS_FAILED

    message = Message.objects.select_related('org').get(pk=message_id)
    contacts = [c.uuid for c in message.recipients.all()]

    client = get_client(message.org)

    # Can only send up to 100 messages at a time
    while contacts:
        try:
            client.create_broadcast(message.text, contacts=contacts[:100])
        except Exception:
            message.status = STATUS_FAILED
            message.save(update_fields=('status',))

            logger.error("Sending message %d failed" % message.pk, exc_info=1)
            return
        contacts = contacts[100:]

    logger.info("Sent message %d from user #%d" % (message.pk, message.sent_by.pk))
    message.status = STATUS_SENT
    message.save(update_fields=('status',))


@task
def send_unsolicited_message(org, text, contact):

    client = get_client(org)

    try:
        client.create_broadcast(text=text, contacts=[contact.uuid])

        logger.info("Sent unsolicited message response to %s" % (contact.name))
    except Exception:

        logger.error("Error sending unsolicited message to %s failed" % (contact.name), exc_info=1)


class FetchOrgInboxMessages(OrgTask):

    def org_task(self, org):
        from .models import InboxMessage
        from tracpro.contacts.models import Contact

        def get_or_create_message(message, org):
            contact = Contact.objects.filter(uuid=message.contact.uuid).first()
            # If the contact sync task hasn't gotten this contact yet,
            # don't get the message yet
            if contact:
                InboxMessage.objects.get_or_create(
                    rapidpro_message_id=message.id,
                    org=org,
                    contact=contact,
                    text=message.text,
                    archived=False,
                    created_on=message.created_on,
                    sent_on=message.sent_on,
                    direction=message.direction[0],
                )

        client = get_client(org)

        # Get non-archived, incoming inbox messages from the past week only
        # because getting all messages was taking too long
        last_week = timezone.now() - relativedelta(days=7)
        # When this is called by the form, we also want to get the very recent sent messages
        one_minute_ago = timezone.now() - relativedelta(minutes=1)
        inbox_messages = client.get_messages(folder='inbox', after=last_week)
        sent_messages = client.get_messages(folder='sent', after=one_minute_ago)

        for inbox_message in inbox_messages:
            get_or_create_message(
                message=inbox_message,
                org=org,
                )
        for sent_message in sent_messages:
            get_or_create_message(
                message=sent_message,
                org=org,
                )
