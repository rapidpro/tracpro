from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from optparse import make_option
from temba.utils import format_iso8601
from tracpro.polls.models import Poll, Response


class Command(BaseCommand):
    args = "org_id [options]"
    option_list = BaseCommand.option_list + (
        make_option('--minutes',
                    action='store',
                    type='int',
                    dest='minutes',
                    default=0,
                    help='Number of previous minutes to fetch'),
        make_option('--hours',
                    action='store',
                    type='int',
                    dest='hours',
                    default=0,
                    help='Number of previous hours to fetch'),
        make_option('--days',
                    action='store',
                    type='int',
                    dest='days',
                    default=0,
                    help='Number of previous days to fetch'),)

    help = 'Fetches old responses for the currently active polls'

    def handle(self, *args, **options):
        org_id = int(args[0]) if args else None
        if not org_id:
            raise CommandError("Most provide valid org id")

        try:
            org = Org.objects.get(pk=org_id)
        except Org.DoesNotExist:
            raise CommandError("No such org with id %d" % org_id)

        minutes, hours, days = options['minutes'], options['hours'], options['days']

        if not (minutes or hours or days):
            raise CommandError("Must provide at least one of --minutes --hours or --days")

        since = timezone.now() - relativedelta(minutes=minutes, hours=hours, days=days)

        self.stdout.write('Fetching responses for org %s since %s...' % (org.name, since.strftime('%b %d, %Y %H:%M')))

        client = org.get_temba_client()

        polls_by_flow_uuids = {p.flow_uuid: p for p in Poll.get_all(org)}

        runs = client.get_runs(flows=polls_by_flow_uuids.keys(), after=since)

        self.stdout.write("Fetched %d runs for org %s" % (len(runs), org.id))

        created = 0
        updated = 0
        for run in runs:
            poll = polls_by_flow_uuids[run.flow]
            try:
                response = Response.from_run(org, run, poll=poll)
            except ValueError, e:
                self.stderr.write("Unable to save run #%d due to error: %s" % (run.id, e.message))
                continue

            if getattr(response, 'is_new', False):
                created += 1
            else:
                updated += 1

        self.stdout.write("Created %d new responses and updated %d existing responses" % (created, updated))
