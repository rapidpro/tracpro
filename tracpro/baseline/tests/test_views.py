from django.core.urlresolvers import reverse
from tracpro.test import TracProTest


class TestBaselineTermCRUDL(TracProTest):

    def test_get(self):
        url_name = "baseline.baselineterm_list"
        self.login(self.admin)
        response = self.url_get('unicef', reverse(url_name))
        self.assertEqual(response.status_code, 200)
