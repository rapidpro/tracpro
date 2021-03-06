from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.utils import timezone

from celery.utils.log import get_task_logger
from djcelery_transactions import task
from django_redis import get_redis_connection

from temba_client.utils import parse_iso8601, format_iso8601

from dash.utils import datetime_to_ms

from tracpro.client import get_client
from tracpro.contacts.models import Contact, NoMatchingCohortsWarning
from tracpro.orgs_ext.tasks import OrgTask

logger = get_task_logger(__name__)

LAST_FETCHED_RUN_TIME_KEY = 'org:%d:last_fetched_run_time'


class FetchOrgRuns(OrgTask):

    def org_task(self, org):
        """
        Fetches new and modified flow runs for the given org and creates/updates
        poll responses.
        """
        from tracpro.orgs_ext.constants import TaskType
        from tracpro.polls.models import Poll, PollRun, Response

        errors = []

        client = get_client(org)
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
        for poll in Poll.objects.active().by_org(org):
            poll_runs = client.get_runs(flow=poll.flow_uuid, after=last_time, before=until, responded=True)
            total_runs += len(poll_runs.all())

            # convert flow "runs" (one per responding contact) into poll responses
            for run in poll_runs:
                try:
                    Response.from_run(org, run, poll=poll)
                except NoMatchingCohortsWarning:
                    # NoMatchingCohorts happens normally so don't complain about that.
                    pass
                except ValueError as e:
                    txt = "Unable to save flow run #%d for contact due to error: %s" % (run.id, e.message)
                    logger.error(txt)
                    errors.append(txt)

        logger.info("Fetched %d new and updated runs for org #%d (since=%s)"
                    % (total_runs, org.id, format_iso8601(last_time) if last_time else 'Never'))

        task_result = dict(time=datetime_to_ms(timezone.now()), counts=dict(fetched=total_runs))
        org.set_task_result(TaskType.fetch_runs, task_result)

        redis_connection.set(last_time_key, format_iso8601(until))
        return errors


@task
def pollrun_start(pollrun_id):
    """
    Starts a newly created pollrun by creating runs in RapidPro and creating
    empty responses for them.
    """
    from tracpro.polls.models import PollRun, Response

    pollrun = PollRun.objects.select_related('poll', 'region').get(pk=pollrun_id)
    if pollrun.pollrun_type not in (PollRun.TYPE_PROPAGATED, PollRun.TYPE_REGIONAL):
        raise ValueError("Can't start non-panel poll")

    org = pollrun.poll.org
    client = get_client(org)

    contacts = Contact.objects.active()
    if pollrun.pollrun_type == PollRun.TYPE_PROPAGATED:
        descendants = pollrun.region.get_descendants(include_self=True)
        contacts = contacts.filter(region__in=descendants)
    elif pollrun.pollrun_type == PollRun.TYPE_REGIONAL:
        contacts = contacts.filter(region=pollrun.region)
    contact_uuids = list(contacts.values_list('uuid', flat=True))

    runs = []
    # There's a limit of 100 contacts per call to create_flow_start (why?)
    while len(contact_uuids):
        runs.extend(
            client.create_flow_start(
                flow=pollrun.poll.flow_uuid, urns=None, contacts=contact_uuids[:100],
                restart_participants=True)
        )
        contact_uuids = contact_uuids[100:]

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
        raise ValueError("Can't restart participants of a non-panel poll")

    if not pollrun.is_last_for_region(pollrun.region):
        raise ValueError("Can only restart last pollrun of poll for a panel")

    org = pollrun.poll.org
    client = get_client(org)

    runs = client.create_flow_start(
        flow=pollrun.poll.flow_uuid, contacts=contact_uuids, restart_participants=True)
    for run in runs:
        Response.create_empty(org, pollrun, run)

    logger.info("Created %d restart runs for poll pollrun #%d" % (len(runs), pollrun.pk))


class SyncOrgPolls(OrgTask):

    def org_task(self, org):
        """
        Syncs Poll info and removes any Polls (and associated questions) that
        are no longer on the remote.
        """
        apps.get_model('polls', 'Poll').objects.sync(org)


@task
def sync_questions_categories(org, polls):
    # Create new or update SELECTED Polls to match RapidPro data.
    from tracpro.polls.models import Question

    # Save the associated Questions for this poll here
    # now that these polls have been activated for the Org
    flow_uuids = [poll.flow_uuid for poll in polls]
    total_polls = len(flow_uuids)
    polls_by_uuid = {poll.flow_uuid: poll for poll in polls}

    logger.info(
        "Retrieving Questions and Categories for %d Poll(s) that were recently updated via the interface." %
        (total_polls))

    result = get_client(org).get_definitions(flows=flow_uuids)
    flows = result.flows
    num_synced = 0

    for flow in flows:
        uuid = flow['metadata']['uuid']
        if uuid not in flow_uuids:
            # We didn't ask for this flow. I don't know why this happens, but it does;
            # just ignore it quietly.
            continue

        poll = polls_by_uuid[uuid]

        logger.info("Retrieving questions and categories for flow %s (%s)" % (poll.flow_uuid, poll.name))

        # Sync related Questions, and maintain question order.
        rule_sets = flow['rule_sets']

        # Remove Questions that are no longer on RapidPro.
        rule_uuids = [rset['uuid'] for rset in rule_sets]
        poll.questions.exclude(ruleset_uuid__in=rule_uuids).delete()

        # Create new or update existing Questions to match RapidPro data.
        for order, rule_set in enumerate(rule_sets, 1):
            Question.objects.from_temba(poll=poll, temba_question=rule_set, order=order)

        num_synced += 1

    logger.info("Completed retrieving Questions and Categories for %d Poll(s)." % (num_synced))
