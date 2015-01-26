from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger
from dash.orgs.models import Org
from dash.utils import parse_iso8601
from djcelery_transactions import task
from redis_cache import get_redis_connection
from tracpro.polls.models import Response

logger = get_task_logger(__name__)

LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


@task
def fetch_all_runs():
    """
    Fetches new flow runs for all orgs
    """
    logger.info("Starting flow run fetch for all orgs...")

    for org in Org.objects.filter(is_active=True).prefetch_related('polls'):
        fetch_org_runs(org.id)


def fetch_org_runs(org):
    client = org.get_temba_client()

    r = get_redis_connection()
    last_time = r.get(LAST_FETCHED_RUN_TIME_KEY % org.pk)
    if last_time is not None:
        last_time = parse_iso8601(last_time)
    else:
        last_run = Response.objects.filter(poll__org=org).order_by('-created_on').first()
        last_time = last_run.created_on if last_run else None

    polls_by_flow_uuids = {p.flow_uuid: p for p in org.polls.all()}

    runs = client.get_runs(flows=polls_by_flow_uuids.keys(), after=last_time)

    logger.info("Fetched %d new runs for org #%d" % (len(runs), org.id))

    if runs:
        last_run = runs[len(runs) - 1]
        r.set(LAST_FETCHED_RUN_TIME_KEY % org.pk, last_run.created_on)

        # convert flow runs into poll responses
        for run in runs:
            poll = polls_by_flow_uuids[run.flow]
            Response.from_run(poll, run)
