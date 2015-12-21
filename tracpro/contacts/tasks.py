from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.utils import timezone

from celery.utils.log import get_task_logger
from djcelery_transactions import task

from dash.utils import datetime_to_ms
from dash.utils.sync import sync_pull_contacts, sync_push_contact

from tracpro.orgs_ext.utils import ActiveOrgsTaskScheduler, OrgTask


logger = get_task_logger(__name__)


@task
def push_contact_change(contact_id, change_type):
    """
    Task to push a local contact change to RapidPro
    """
    from tracpro.groups.models import Group, Region
    from .models import Contact

    contact = Contact.objects.select_related('org', 'region').get(pk=contact_id)
    org = contact.org

    logger.info("Pushing %s change to contact %s" % (change_type.name.upper(), contact.uuid))

    region_uuids = set([r.uuid for r in Region.get_all(org)])
    group_uuids = set([r.uuid for r in Group.get_all(org)])

    sync_push_contact(org, contact, change_type, [region_uuids, group_uuids])


@task
class SyncOrgContacts(OrgTask):

    def org_task(self, org):
        from tracpro.groups.models import Region, Group
        from tracpro.orgs_ext.constants import TaskType
        from .models import Contact

        logger.info('Starting contact sync task for org #%d' % org.id)

        sync_groups = [r.uuid for r in Region.get_all(org)] + [g.uuid for g in Group.get_all(org)]

        most_recent_contact = Contact.objects.by_org(org).active().exclude(temba_modified_on=None)
        most_recent_contact = most_recent_contact.order_by('-temba_modified_on').first()
        if most_recent_contact:
            last_time = most_recent_contact.temba_modified_on
        else:
            last_time = None

        created, updated, deleted, failed = sync_pull_contacts(
            org, Contact, fields=(), groups=sync_groups, last_time=last_time,
            delete_blocked=True)

        task_result = dict(time=datetime_to_ms(timezone.now()),
                           counts=dict(created=len(created),
                                       updated=len(updated),
                                       deleted=len(deleted),
                                       failed=len(failed)))
        org.set_task_result(TaskType.sync_contacts, task_result)

        logger.info("Finished contact sync for org #%d (%d created, "
                    "%d updated, %d deleted, %d failed)" %
                    (org.id, len(created), len(updated), len(deleted), len(failed)))


@task
class SyncAllContacts(ActiveOrgsTaskScheduler):
    task = SyncOrgContacts


@task
class SyncOrgDataFields(OrgTask):

    def org_task(self, org):
        """
        Syncs DataField info and removes any DataFields (and associated
        contact values) that are no longer on the remote.
        """
        apps.get_model('contacts', 'DataField').objects.sync(org)


@task
class SyncAllDataFields(ActiveOrgsTaskScheduler):
    task = SyncOrgDataFields
