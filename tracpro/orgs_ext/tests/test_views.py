from __future__ import absolute_import, unicode_literals

import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
import mock
from django.utils import timezone

from tracpro.test.cases import TracProDataTest


class TestOrgExtCRUDLHome(TracProDataTest):
    url_name = "orgs_ext.org_home"

    def test_get(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)


class FetchRunsViewTest(TracProDataTest):
    url_name = 'orgs_ext.org_fetchruns'

    def setUp(self):
        super(FetchRunsViewTest, self).setUp()
        self.login(self.superuser)

    def test_get(self):
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)

    def test_get_not_logged_in(self):
        self.client.logout()
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL + "?next", response['Location'])

    def test_get_not_superuser(self):
        self.client.logout()
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL + "?next", response['Location'])

    def test_post_no_data(self):
        response = self.url_post(
            'unicef',
            reverse(self.url_name),
            data={}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'days', [u'This field is required.'])

    def test_post_bad_data(self):
        response = self.url_post(
            'unicef',
            reverse(self.url_name),
            data={
                'days': 'three'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'days', [u'Enter a whole number.'])

    @mock.patch('tracpro.orgs_ext.views.tasks.fetch_runs.delay')
    def test_post_good_data(self, mock_fetchruns):
        since = timezone.now() - datetime.timedelta(days=3)
        response = self.url_post(
            'unicef',
            reverse(self.url_name),
            data={
                'days': '3'
            }
        )
        if response.status_code != 302:
            self.assertFalse(response.context['form'].errors)
        self.assertEqual(response.status_code, 302)
        mock_fetchruns.assert_called_with(self.unicef.id, mock.ANY, self.superuser.email)
        args, kwargs = mock_fetchruns.call_args
        since_arg = args[1]
        self.assertEqual(
            since.replace(hour=0, minute=0, second=0, microsecond=0),
            since_arg.replace(hour=0, minute=0, second=0, microsecond=0),
        )
