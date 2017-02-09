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
        client.create_broadcast(text, contacts=[contact.uuid])

        logger.info("Sent unsolicited message response to %s" % (contact.name))
    except Exception:

        logger.error("Error sending unsolicited message to %s failed" % (contact.name), exc_info=1)


class FetchOrgInboxMessages(OrgTask):

    def org_task(self, org):
        from .models import InboxMessage
        from tracpro.contacts.models import Contact

        client = get_client(org)

        # Get non-archived, incoming inbox messages from the past week only
        # because getting all messages was taking too long
        last_week = timezone.now() - relativedelta(days=7)
        inbox_messages = client.get_messages(folder='inbox', after=last_week)

        for inbox_message in inbox_messages:
            contact = Contact.objects.filter(uuid=inbox_message.contact.uuid).first()
            # If the contact sync task hasn't gotten this contact yet,
            # don't get the message yet
            if contact:
                inbox_message_record = InboxMessage.objects.filter(
                    rapidpro_message_id=inbox_message.id)
                if inbox_message_record:
                    inbox_message_record.update(
                        org=org,
                        contact=contact,
                        text=inbox_message.text,
                        archived=False,
                        created_on=inbox_message.created_on,
                        sent_on=inbox_message.sent_on,
                        direction=inbox_message.direction,
                    )
                else:
                    InboxMessage.objects.create(
                        org=org,
                        rapidpro_message_id=inbox_message.id,
                        contact=contact,
                        text=inbox_message.text,
                        archived=False,
                        created_on=inbox_message.created_on,
                        sent_on=inbox_message.sent_on,
                        direction=inbox_message.direction,
                    )
