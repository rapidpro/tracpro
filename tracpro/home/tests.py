from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from tracpro.test import TracProTest


class HomeViewTest(TracProTest):
    def test_home(self):
        # can't access it anonymously
        response = self.url_get('unicef', reverse('home.home'))
        self.assertLoginRedirect(response, 'unicef', '/')

        # login as superuser
        self.login(self.superuser)

        # can access, but can't chat
        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['regions']), 0)

        # login as administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r.name for r in response.context['regions']], ["Kandahar", "Khost", "Kunar"])

        # login as regular user
        self.login(self.user1)

        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r.name for r in response.context['regions']], ["Kandahar"])
