from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger
from dash.orgs.models import Org
from django.db.models import Max
from djcelery_transactions import task
from redis_cache import get_redis_connection
from temba.utils import parse_iso8601, format_iso8601
from tracpro.polls.models import Poll, Issue, Response

logger = get_task_logger(__name__)

LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


@task
def fetch_all_new_runs():
    """
    Fetches new flow runs for all orgs
    """
    logger.info("Starting flow run fetch for all orgs...")

    for org in Org.objects.filter(is_active=True).prefetch_related('polls'):
        fetch_org_new_runs(org)
        fetch_org_updated_runs(org)


def fetch_org_new_runs(org):
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
            Response.get_or_create(org, run, poll=poll)

    if newest_run:
        r.set(last_time_key, format_iso8601(newest_run.created_on))


def fetch_org_updated_runs(org):
    """
    Fetches updated runs for incomplete responses
    """
    client = org.get_temba_client()

    incomplete_responses = Response.get_update_required(org)

    if incomplete_responses:
        runs = client.get_runs(ids=[r.flow_run_id for r in incomplete_responses])

        logger.info("Fetched %d runs for incomplete responses" % len(runs))

        polls_by_flow_uuids = {p.flow_uuid: p for p in Poll.get_all(org)}

        for run in runs:
            poll = polls_by_flow_uuids[run.flow]
            Response.get_or_create(org, run, poll=poll)
    else:
        logger.info("No incomplete responses to update")


@task
def restart_participants(issue_id, contact_uuids):
    """
    Restarts the given contacts in the given poll issue
    """
    issue = Issue.objects.select_related('poll').get(pk=issue_id)
    org = issue.poll.org
    client = org.get_temba_client()

    # TODO
