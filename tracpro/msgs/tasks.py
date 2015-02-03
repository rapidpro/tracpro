from __future__ import unicode_literals

from celery.utils.log import get_task_logger
from djcelery_transactions import task

logger = get_task_logger(__name__)


@task
def send_message(message_id):
    from .models import Message, STATUS_SENT, STATUS_FAILED

    message = Message.objects.select_related('org', 'user').get(pk=message_id)

    client = message.org.get_temba_client()

    try:
        client.create_broadcast(message.text, contacts=[c.uuid for c in message.recipients])

        message.status = STATUS_SENT
        message.save(update_fields=('status',))

        logger.info("Sent message %d from user #%d" % (message.pk, message.user.pk))
    except Exception:
        message.status = STATUS_FAILED
        message.save(update_fields=('status',))

        logger.error("Sending message %d failed" % message.pk, exc_info=1)
