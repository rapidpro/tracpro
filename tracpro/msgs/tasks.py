from __future__ import unicode_literals

from celery.utils.log import get_task_logger
from djcelery_transactions import task

from dash.orgs.models import Org

logger = get_task_logger(__name__)


@task
def send_message(message_id):
    from .models import Message, STATUS_SENT, STATUS_FAILED

    message = Message.objects.select_related('org').get(pk=message_id)

    client = message.org.get_temba_client()

    try:
        client.create_broadcast(message.text, contacts=[c.uuid for c in message.recipients.all()])

        message.status = STATUS_SENT
        message.save(update_fields=('status',))

        logger.info("Sent message %d from user #%d" % (message.pk, message.sent_by.pk))
    except Exception:
        message.status = STATUS_FAILED
        message.save(update_fields=('status',))

        logger.error("Sending message %d failed" % message.pk, exc_info=1)

@task
def fetch_all_inbox_messages():
    """
    Fetches all unsolicited inbox messages (type="I") into InboxMessage
    """
    logger.info("Starting inbox message fetch for all orgs...")

    for org in Org.objects.filter(is_active=True):
        fetch_inbox_messages(org)

def fetch_inbox_messages(org):
    from .models import InboxMessage
    from tracpro.contacts.models import Contact

    client = org.get_temba_client()

    inbox_messages = client.get_messages(_types="I")

    for inbox_message in inbox_messages:
        contact = Contact.objects.filter(
                        uuid=inbox_message.contact
                        ).first()
        # If the sync_all_contacts() task hasn't gotten this contact yet,
        # don't get the message yet
        if contact:
            inbox_message_record = InboxMessage.objects.filter(rapidpro_message_id=inbox_message.id)
            if inbox_message_record:
                inbox_message_record.update(
                    org=org,
                    contact_from=contact,
                    text=inbox_message.text,
                    archived=inbox_message.archived,
                    created_on=inbox_message.created_on,
                    delivered_on=inbox_message.delivered_on,
                    sent_on=inbox_message.sent_on
                    )
            else:
                InboxMessage.objects.create(
                    org=org,
                    rapidpro_message_id=inbox_message.id,
                    contact_from=contact,
                    text=inbox_message.text,
                    archived=inbox_message.archived,
                    created_on=inbox_message.created_on,
                    delivered_on=inbox_message.delivered_on,
                    sent_on=inbox_message.sent_on
                    )