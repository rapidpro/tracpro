import mock
from django.utils import timezone
from temba_client.types import Run
from tracpro.orgs_ext.tasks import fetch_runs
from tracpro.test.cases import TracProDataTest


class FetchRunsTaskTest(TracProDataTest):
    def test_bad_org(self):
        with self.assertRaises(ValueError):
            fetch_runs(0, timezone.now())

    @mock.patch('tracpro.orgs_ext.tasks.logger.error')
    @mock.patch('tracpro.orgs_ext.tasks.logger.info')
    def test_no_runs(self, mock_info_logger, mock_error_logger):
        org = self.unicef
        client = self.mock_temba_client
        client.get_runs.return_value = []
        flow_id = self.poll1.flow_uuid
        fetch_runs(org.id, timezone.now())

        # runs = client.get_runs(flows=polls_by_flow_uuids.keys(), after=since)
        client.get_runs.assert_called_with(flows=[flow_id], after=mock.ANY)
        self.assertEqual(mock_info_logger.call_args_list[-2], (("Fetched 0 runs for org %s" % org.id,),))
        mock_info_logger.assert_called_with("Created 0 new responses and updated 0 existing responses.")
        self.assertFalse(mock_error_logger.call_count)

    @mock.patch('tracpro.orgs_ext.tasks.logger.error')
    @mock.patch('tracpro.orgs_ext.tasks.logger.info')
    def test_with_runs(self, mock_info_logger, mock_error_logger):
        org = self.unicef
        client = self.mock_temba_client
        flow_id = self.poll1.flow_uuid
        run1 = Run.create(id=123, contact=self.contact1.uuid, flow=flow_id, created_on=timezone.now(), values=[])
        run2 = Run.create(id=123, contact=self.contact1.uuid, flow='nonesuch', created_on=timezone.now(), values=[])
        client.get_runs.return_value = [run1, run2]
        fetch_runs(org.id, timezone.now())

        # runs = client.get_runs(flows=polls_by_flow_uuids.keys(), after=since)
        client.get_runs.assert_called_with(flows=[flow_id], after=mock.ANY)
        # We pretended to return 2 runs from the client:
        self.assertEqual(mock_info_logger.call_args_list[-2], (("Fetched 2 runs for org %s" % org.id,),))
        # Only one of our runs was for one of our polls
        mock_info_logger.assert_called_with("Created 1 new responses and updated 0 existing responses.")
        self.assertFalse(mock_error_logger.call_count)
