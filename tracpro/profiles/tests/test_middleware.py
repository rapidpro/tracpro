from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from tracpro.test.cases import TracProDataTest


class ForcePasswordChangeMiddlewareTest(TracProDataTest):

    def test_process_view(self):
        self.user1.profile.change_password = True
        self.user1.profile.save()

        self.login(self.user1)

        response = self.url_get('unicef', reverse('home.home'))
        self.assertRedirects(
            response,
            'http://unicef.testserver/profile/self/',
            fetch_redirect_response=False)

        response = self.url_get('unicef', reverse('profiles.user_self'))
        self.assertEqual(response.status_code, 200)

        self.user1.profile.change_password = False
        self.user1.profile.save()

        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 200)
