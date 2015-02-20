from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger
from dash.orgs.models import Org
from dash.utils import datetime_to_ms
from dash.utils.sync import sync_pull_contacts, sync_push_contact
from django.utils import timezone
from djcelery_transactions import task

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
def sync_org_contacts(org_id):
    """
    Syncs all contacts for the given org
    """
    from tracpro.groups.models import Region, Group
    from tracpro.orgs_ext import TaskType
    from .models import Contact

    org = Org.objects.get(pk=org_id)

    logger.info('Starting contact sync task for org #%d' % org.id)

    sync_groups = [r.uuid for r in Region.get_all(org)] + [g.uuid for g in Group.get_all(org)]

    created, updated, deleted, failed = sync_pull_contacts(org, Contact, fields=(), groups=sync_groups)

    task_result = dict(time=datetime_to_ms(timezone.now()),
                       counts=dict(created=len(created),
                                   updated=len(updated),
                                   deleted=len(deleted),
                                   failed=len(failed)))
    org.set_task_result(TaskType.sync_contacts, task_result)

    logger.info("Finished contact sync for org #%d (%d created, %d updated, %d deleted, %d failed)"
                % (org.id, len(created), len(updated), len(deleted), len(failed)))


@task
def sync_all_contacts():
    """
    Syncs all contacts for all orgs
    """
    logger.info("Starting contact sync for all orgs...")

    for org in Org.objects.filter(is_active=True):
        sync_org_contacts(org.id)
