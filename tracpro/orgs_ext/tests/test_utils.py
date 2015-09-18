import mock
from requests import HTTPError

from django.test import TestCase

from temba.base import TembaAPIError

from tracpro.test import factories

from .. import utils


class TestRunOrgTask(TestCase):

    def setUp(self):
        super(TestRunOrgTask, self).setUp()
        self.mock_task = mock.Mock(return_value="hello")
        self.org = factories.Org(api_token="token")

    def test_org_with_api_token(self):
        """Return result of task if API token is valid."""
        result = utils.run_org_task(self.org, self.mock_task)
        self.assertEqual(result, "hello")
        self.mock_task.assert_called_once_with(self.org.pk)

    def test_org_with_blank_api_token(self):
        """Do not call task function if API token is blank."""
        self.org.api_token = ""
        result = utils.run_org_task(self.org, self.mock_task)
        self.assertIsNone(result)
        self.mock_task.assert_not_called()

    def test_org_with_null_api_token(self):
        """Do not cal task function if API token is null."""
        self.org.api_token = None
        result = utils.run_org_task(self.org, self.mock_task)
        self.assertIsNone(result)
        self.mock_task.assert_not_called()

    def test_org_with_invalid_api_token(self):
        """Handle invalid API token exception."""
        def side_effect(org_id):
            err = HTTPError()
            err.response = mock.Mock(status_code=403)
            raise TembaAPIError(caused_by=err)

        self.mock_task.side_effect = side_effect
        result = utils.run_org_task(self.org, self.mock_task)
        self.assertIsNone(result)
        self.mock_task.assert_called_once_with(self.org.pk)

    def test_org_task_unknown_exception(self):
        """Raise unknown errors."""
        self.mock_task.side_effect = Exception
        with self.assertRaises(Exception):
            utils.run_org_task(self.org, self.mock_task)
        self.mock_task.assert_called_once_with(self.org.pk)
