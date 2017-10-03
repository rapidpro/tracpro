from __future__ import absolute_import, unicode_literals

from django.apps import apps

from celery.utils.log import get_task_logger
from djcelery_transactions import task

from tracpro.orgs_ext.tasks import OrgTask
from tracpro.contacts.utils import sync_push_contact


logger = get_task_logger(__name__)


@task
def push_contact_change(contact_id, change_type):
    """
    Task to push a local contact change to RapidPro
    """
    from .models import Contact

    contact = Contact.objects.select_related('org', 'region').get(pk=contact_id)
    org = contact.org

    logger.info("Pushing %s change to contact %s" % (change_type.name.upper(), contact.uuid))

    sync_push_contact(org, contact, change_type)


class SyncOrgContacts(OrgTask):

    def org_task(self, org):
        apps.get_model('contacts', 'Contact').objects.sync(org)


class SyncOrgDataFields(OrgTask):

    def org_task(self, org):
        """
        Syncs DataField info and removes any DataFields (and associated
        contact values) that are no longer on the remote.
        """
        apps.get_model('contacts', 'DataField').objects.sync(org)
