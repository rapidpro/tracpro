from django.core.urlresolvers import reverse

from tracpro.test.cases import TracProDataTest


class UserRegionsMiddlewareTest(TracProDataTest):
    def test_process_request(self):
        # make anonymous request to home page
        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 302)

        # admin user with implicit access to all regions
        self.login(self.admin)

        # default to "All Regions"
        response = self.url_get('unicef', reverse('home.home'))
        self.assertIsNone(self.client.session['region'])

        # check region menu...
        self.assertContains(response, "Kandahar", status_code=200)
        self.assertContains(response, "Khost")
        self.assertContains(response, "Kunar")
        self.assertContains(response, "All Regions")

        # should come from session this time
        self.url_get('unicef', reverse('home.home'))
        self.assertIsNone(self.client.session['region'])

        # any page allows region to be set via _region param
        self.url_get('unicef', reverse('home.home'), {'_region': self.region3.pk})
        self.assertEqual(self.client.session['region'], self.region3.pk)

        # can set to region to 0 meaning "All Regions"
        self.url_get('unicef', reverse('home.home'), {'_region': 0})
        self.assertIsNone(self.client.session['region'])

        # user with access to 2 regions (#2 and #3)
        self.login(self.user2)

        # default to first region A-Z
        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(self.client.session['region'], self.region2.pk)

        # check region menu...
        self.assertContains(response, "Khost", status_code=200)
        self.assertContains(response, "Kunar")
        self.assertNotContains(response, "All Regions")

        # can't set to region that user doesn't have access, so defaults back to first
        self.url_get('unicef', reverse('home.home'), {'_region': self.region1.pk})
        self.assertEqual(self.client.session['region'], self.region2.pk)

        # user with access to only 1 region
        self.login(self.user1)

        # user only has access to region #1 so should default to region #1
        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(self.client.session['region'], self.region1.pk)

        # no region menu, just region name
        self.assertContains(response, "Kandahar", status_code=200)
        self.assertNotContains(response, "All Regions")
