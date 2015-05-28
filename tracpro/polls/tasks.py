from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger
from dash.orgs.models import Org
from dash.utils import datetime_to_ms, chunks
from django.utils import timezone
from djcelery_transactions import task
from redis_cache import get_redis_connection
from temba.utils import parse_iso8601, format_iso8601

logger = get_task_logger(__name__)

LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


@task
def fetch_all_runs():
    """
    Fetches flow runs for all orgs
    """
    logger.info("Starting flow run fetch for all orgs...")

    for org in Org.objects.filter(is_active=True).prefetch_related('polls'):
        fetch_org_runs(org)


def fetch_org_runs(org):
    """
    Fetches flow runs for the given org
    """
    from tracpro.orgs_ext import TaskType

    fetch_org_new_runs(org)
    fetch_org_updated_runs(org)

    task_result = dict(time=datetime_to_ms(timezone.now()))
    org.set_task_result(TaskType.fetch_runs, task_result)


def fetch_org_new_runs(org):
    from tracpro.polls.models import Poll, Response

    client = org.get_temba_client()
    r = get_redis_connection()
    last_time_key = LAST_FETCHED_RUN_TIME_KEY % org.pk

    newest_run = None
    last_time = r.get(last_time_key)
    if last_time is not None:
        last_time = parse_iso8601(last_time)
    else:
        newest_run = Response.objects.filter(issue__poll__org=org).order_by('-created_on').first()
        last_time = newest_run.created_on if newest_run else None

    polls_by_flow_uuids = {p.flow_uuid: p for p in Poll.get_all(org)}

    runs = client.get_runs(flows=polls_by_flow_uuids.keys(), after=last_time)

    if runs:
        # because the Temba API compares after dates with gte, oldest run will be usually be a duplicate
        oldest_run = runs[len(runs) - 1]
        if Response.objects.filter(flow_run_id=oldest_run.id).exists():
            runs = runs[0:-1]

    logger.info("Fetched %d new runs for org #%d (after=%s)"
                % (len(runs), org.id, format_iso8601(last_time) if last_time else 'Never'))

    if runs:
        newest_run = runs[0]

        # convert flow runs into poll responses
        for run in runs:
            poll = polls_by_flow_uuids[run.flow]
            try:
                Response.from_run(org, run, poll=poll)
            except ValueError, e:
                logger.error("Unable to save run #%d due to error: %s" % (run.id, e.message))
                continue

    if newest_run:
        r.set(last_time_key, format_iso8601(newest_run.created_on))


def fetch_org_updated_runs(org):
    """
    Fetches updated runs for incomplete responses
    """
    from tracpro.polls.models import Poll, Response

    client = org.get_temba_client()

    incomplete_responses = Response.get_update_required(org)

    max_number_fetchable_runs = 50  # Not yet sure what the optimum can be in order to make the smallest number of requests.

    if incomplete_responses:
        runs = []
        for resp_chunk in chunks(list(incomplete_responses), max_number_fetchable_runs):
            runs += client.get_runs(ids=[r.flow_run_id for r in resp_chunk])

        logger.info("Fetched %d runs for incomplete responses" % len(runs))

        polls_by_flow_uuids = {p.flow_uuid: p for p in Poll.get_all(org)}

        for run in runs:
            poll = polls_by_flow_uuids[run.flow]
            Response.from_run(org, run, poll=poll)
    else:
        logger.info("No incomplete responses to update")


@task
def issue_start(issue_id):
    """
    Starts a newly created issue by creating runs in RapidPro and creating empty responses for them.
    """
    from tracpro.polls.models import Issue, Response

    issue = Issue.objects.select_related('poll', 'region').get(pk=issue_id)
    if not issue.region:
        raise ValueError("Can't start non-regional poll")

    org = issue.poll.org
    client = org.get_temba_client()

    contact_uuids = [c.uuid for c in issue.region.get_contacts()]

    runs = client.create_runs(issue.poll.flow_uuid, contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, issue, run)

    logger.info("Created %d new runs for new poll issue #%d" % (len(runs), issue.pk))


@task
def issue_restart_participants(issue_id, contact_uuids):
    """
    Restarts the given contacts in the given poll issue by replacing any existing response they have with an empty one.
    """
    from tracpro.polls.models import Issue, Response

    issue = Issue.objects.select_related('poll').get(pk=issue_id)
    if not issue.region:
        raise ValueError("Can't restart participants of a non-regional poll")

    if not issue.is_last_for_region(issue.region):
        raise ValueError("Can only restart last issue of poll for a region")

    org = issue.poll.org
    client = org.get_temba_client()

    runs = client.create_runs(issue.poll.flow_uuid, contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, issue, run)

    logger.info("Created %d restart runs for poll issue #%d" % (len(runs), issue.pk))
