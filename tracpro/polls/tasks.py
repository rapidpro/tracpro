from __future__ import absolute_import, unicode_literals

from django.utils import timezone

from celery.utils.log import get_task_logger
from djcelery_transactions import task
from django_redis import get_redis_connection
from temba.utils import parse_iso8601, format_iso8601

from dash.utils import datetime_to_ms
from dash.orgs.models import Org

logger = get_task_logger(__name__)

FETCH_ALL_RUNS_LOCK = 'task:fetch_all_runs'
LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


@task
def fetch_all_runs():
    """
    Fetches flow runs for all orgs
    """
    r = get_redis_connection()

    # only do this if we aren't already running so we don't get backed up
    if not r.get(FETCH_ALL_RUNS_LOCK):
        with r.lock(FETCH_ALL_RUNS_LOCK, timeout=600):
            logger.info("Starting flow run fetch for all orgs...")

            for org in Org.objects.filter(is_active=True).prefetch_related('polls'):
                fetch_org_runs(org)
    else:
        logger.warn("Skipping run fetch as it is already running")


def fetch_org_runs(org):
    """
    Fetches new and modified flow runs for the given org and creates/updates poll responses
    """
    from tracpro.orgs_ext.constants import TaskType
    from tracpro.polls.models import Poll, Response

    client = org.get_temba_client()
    r = get_redis_connection()
    last_time_key = LAST_FETCHED_RUN_TIME_KEY % org.pk
    last_time = r.get(last_time_key)

    if last_time is not None:
        last_time = parse_iso8601(last_time)
    else:
        newest_run = Response.objects.filter(pollrun__poll__org=org).order_by('-created_on').first()
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
            except ValueError, e:
                logger.error("Unable to save run #%d due to error: %s" % (run.id, e.message))
                continue

    logger.info("Fetched %d new and updated runs for org #%d (since=%s)"
                % (total_runs, org.id, format_iso8601(last_time) if last_time else 'Never'))

    task_result = dict(time=datetime_to_ms(timezone.now()), counts=dict(fetched=total_runs))
    org.set_task_result(TaskType.fetch_runs, task_result)

    r.set(last_time_key, format_iso8601(until))


@task
def pollrun_start(pollrun_id):
    """
    Starts a newly created pollrun by creating runs in RapidPro and creating
    empty responses for them.
    """
    from tracpro.polls.models import PollRun, Response

    pollrun = PollRun.objects.select_related('poll', 'region').get(pk=pollrun_id)
    if not pollrun.region:
        raise ValueError("Can't start non-regional poll")

    org = pollrun.poll.org
    client = org.get_temba_client()

    contact_uuids = [c.uuid for c in pollrun.region.get_contacts()]

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

    pollrun = PollRun.objects.select_related('poll').get(pk=pollrun_id)
    if not pollrun.region:
        raise ValueError("Can't restart participants of a non-regional poll")

    if not pollrun.is_last_for_region(pollrun.region):
        raise ValueError("Can only restart last pollrun of poll for a region")

    org = pollrun.poll.org
    client = org.get_temba_client()

    runs = client.create_runs(pollrun.poll.flow_uuid, contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, pollrun, run)

    logger.info("Created %d restart runs for poll pollrun #%d" % (len(runs), pollrun.pk))
