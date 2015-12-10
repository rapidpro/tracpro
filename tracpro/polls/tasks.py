from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.utils import timezone

from celery.utils.log import get_task_logger
from djcelery_transactions import task
from django_redis import get_redis_connection

from temba_client.utils import parse_iso8601, format_iso8601

from dash.orgs.models import Org
from dash.utils import datetime_to_ms

from tracpro.contacts.models import Contact
from tracpro.orgs_ext.utils import run_org_task


logger = get_task_logger(__name__)

FETCH_ALL_RUNS_LOCK = 'task:fetch_all_runs'

LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


@task
def fetch_all_runs():
    """Fetches flow runs for all orgs."""
    redis_connection = get_redis_connection()

    # only do this if we aren't already running so we don't get backed up
    if not redis_connection.get(FETCH_ALL_RUNS_LOCK):
        with redis_connection.lock(FETCH_ALL_RUNS_LOCK, timeout=600):
            logger.info("Starting flow run fetch for all orgs...")

            for org in Org.objects.filter(is_active=True).prefetch_related('polls'):
                run_org_task(org, fetch_org_runs)
    else:
        logger.warn("Skipping run fetch as it is already running")


def fetch_org_runs(org_id):
    """
    Fetches new and modified flow runs for the given org and creates/updates
    poll responses.
    """
    from tracpro.orgs_ext.constants import TaskType
    from tracpro.polls.models import Poll, PollRun, Response

    org = Org.objects.get(pk=org_id)

    client = org.get_temba_client()
    redis_connection = get_redis_connection()
    last_time_key = LAST_FETCHED_RUN_TIME_KEY % org.pk
    last_time = redis_connection.get(last_time_key)

    if last_time is not None:
        last_time = parse_iso8601(last_time)
    else:
        newest_runs = Response.objects.filter(pollrun__poll__org=org).order_by('-created_on')
        newest_runs = newest_runs.exclude(pollrun__pollrun_type=PollRun.TYPE_SPOOFED)
        newest_run = newest_runs.first()
        last_time = newest_run.created_on if newest_run else None

    until = timezone.now()

    total_runs = 0
    for poll in Poll.get_all(org):
        poll_runs = client.get_runs(flows=[poll.flow_uuid], after=last_time, before=until)
        total_runs += len(poll_runs)

        # convert flow runs into poll responses
        for run in poll_runs:
            try:
                Response.from_run(org, run, poll=poll)
            except ValueError as e:
                logger.error("Unable to save run #%d due to error: %s" % (run.id, e.message))
                continue

    logger.info("Fetched %d new and updated runs for org #%d (since=%s)"
                % (total_runs, org.id, format_iso8601(last_time) if last_time else 'Never'))

    task_result = dict(time=datetime_to_ms(timezone.now()), counts=dict(fetched=total_runs))
    org.set_task_result(TaskType.fetch_runs, task_result)

    redis_connection.set(last_time_key, format_iso8601(until))


@task
def pollrun_start(pollrun_id):
    """
    Starts a newly created pollrun by creating runs in RapidPro and creating
    empty responses for them.
    """
    from tracpro.polls.models import PollRun, Response

    pollrun = PollRun.objects.select_related('poll', 'region').get(pk=pollrun_id)
    if pollrun.pollrun_type not in (PollRun.TYPE_PROPAGATED, PollRun.TYPE_REGIONAL):
        raise ValueError("Can't start non-regional poll")

    org = pollrun.poll.org
    client = org.get_temba_client()

    contacts = Contact.objects.active()
    if pollrun.pollrun_type == PollRun.TYPE_PROPAGATED:
        descendants = pollrun.region.get_descendants(include_self=True)
        contacts = contacts.filter(region__in=descendants)
    elif pollrun.pollrun_type == PollRun.TYPE_REGIONAL:
        contacts = contacts.filter(region=pollrun.region)
    contact_uuids = list(contacts.values_list('uuid', flat=True))

    runs = client.create_runs(pollrun.poll.flow_uuid, contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, pollrun, run)

    logger.info("Created %d new runs for new poll pollrun #%d" % (len(runs), pollrun.pk))


@task
def pollrun_restart_participants(pollrun_id, contact_uuids):
    """
    Restarts the given contacts in the given poll pollrun by replacing any
    existing response they have with an empty one.
    """
    from tracpro.polls.models import PollRun, Response

    pollrun = PollRun.objects.select_related('poll', 'region').get(pk=pollrun_id)
    if pollrun.pollrun_type not in (PollRun.TYPE_REGIONAL, PollRun.TYPE_PROPAGATED):
        raise ValueError("Can't restart participants of a non-regional poll")

    if not pollrun.is_last_for_region(pollrun.region):
        raise ValueError("Can only restart last pollrun of poll for a region")

    org = pollrun.poll.org
    client = org.get_temba_client()

    runs = client.create_runs(pollrun.poll.flow_uuid, contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, pollrun, run)

    logger.info("Created %d restart runs for poll pollrun #%d" % (len(runs), pollrun.pk))


@task
def sync_all_polls():
    logger.info("Syncing Polls for active orgs.")
    for org in Org.objects.filter(is_active=True):
        run_org_task(org, sync_org_polls)
    logger.info("Finished syncing Polls for active orgs.")


@task
def sync_org_polls(org_pk):
    """Sync an org's Polls.

    Syncs Poll info and removes any Polls (and associated questions) that
    are no longer on the remote.
    """
    org = Org.objects.get(pk=org_pk)
    logger.info("Syncing polls for {}.".format(org.name))
    apps.get_model('polls', 'Poll').objects.sync(org)
    logger.info("Finished syncing polls for {}.".format(org.name))
