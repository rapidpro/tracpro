from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from tracpro.test.cases import TracProDataTest


class TestOrgExtCRUDLHome(TracProDataTest):
    url_name = "orgs_ext.org_home"

    def test_get(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
