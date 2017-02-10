from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.core.management.base import BaseCommand

from tracpro.client import get_client
from tracpro.polls.models import FlowDefinition


class Command(BaseCommand):
    args = "org_id [options]"
    help = 'Temporary testbed for API v2 experimentation'

    def handle(self, *args, **options):
        org_id = int(args[0]) if args else None

        org = Org.objects.get(id=org_id)

        client = get_client(org)
        flow_query = client.get_flows()  # temba_client.clients.CursorQuery
        flows = flow_query.all()
        flow = flows[0]
        definitions = client.get_definitions(flows=[flow.uuid])
        defn = FlowDefinition.create(**definitions.flows[0])
        print(defn.rule_sets)
