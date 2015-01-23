from __future__ import absolute_import, unicode_literals

from mock import patch
from temba.types import Flow, FlowRuleSet
from tracpro.test import TracProTest
from .models import Poll


class PollTest(TracProTest):
    @patch('dash.orgs.models.TembaClient.get_flows')
    def test_update_flows(self, mock_get_flows):
        mock_get_flows.return_value = [
            Flow.create(name="Poll #1", uuid='F-001', rulesets=[
                FlowRuleSet.create(uuid='RS-001', label='How old are you'),
                FlowRuleSet.create(uuid='RS-002', label='Where do you live')
            ]),
            Flow.create(name="Poll #2", uuid='F-002', rulesets=[
                FlowRuleSet.create(uuid='RS-003', label='How many goats'),
                FlowRuleSet.create(uuid='RS-004', label='How many sheep')
            ]),
            Flow.create(name="Poll #3", uuid='F-003', rulesets=[
                FlowRuleSet.create(uuid='RS-003', label='What time is it')
            ])
        ]
        Poll.update_flows(self.unicef, ['F-001', 'F-002'])

        self.assertEqual(self.unicef.polls.count(), 2)

        poll1 = Poll.objects.get(flow_uuid='F-001')
        self.assertEqual(poll1.name, "Poll #1")
        self.assertEqual(poll1.questions.count(), 2)
