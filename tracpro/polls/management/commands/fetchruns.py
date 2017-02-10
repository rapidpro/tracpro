from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from django.utils import timezone

from tracpro.orgs_ext.tasks import fetch_runs


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
            raise CommandError("Must provide valid org id")
        if not Org.objects.filter(pk=org_id).exists():
            raise CommandError("No such org with id %d" % org_id)

        minutes, hours, days = options['minutes'], options['hours'], options['days']

        if not (minutes or hours or days):
            raise CommandError("Must provide at least one of --minutes --hours or --days")

        howfarback = relativedelta(
            minutes=minutes,
            hours=hours,
            days=days)
        since = timezone.now() - howfarback

        fetch_runs(org_id, since)
