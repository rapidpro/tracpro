from __future__ import absolute_import, unicode_literals

import json

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup
from tracpro.contacts.models import Contact
from tracpro.groups.models import Region, Group
from tracpro.polls.models import PollRun, Response, RESPONSE_COMPLETE, RESPONSE_PARTIAL, RESPONSE_EMPTY
from tracpro.test import TracProTest


class RegionTest(TracProTest):
    def test_create(self):
        zabul = Region.create(self.unicef, "Zabul", 'G-101')
        jan = self.create_contact(self.unicef, "Jan", 'tel:1234', zabul, self.group1, 'C-101')
        bob = User.create(self.unicef, "Bob", "bob@unicef.org", "pass", False, [zabul])

        self.assertEqual(zabul.org, self.unicef)
        self.assertEqual(zabul.name, "Zabul")
        self.assertEqual(zabul.uuid, 'G-101')
        self.assertEqual(list(zabul.get_contacts()), [jan])
        self.assertEqual(list(zabul.get_users()), [bob])

    def test_get_all(self):
        self.assertEqual(len(Region.get_all(self.unicef)), 3)
        self.assertEqual(len(Region.get_all(self.nyaruka)), 1)

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.get_groups')
    @patch('dash.orgs.models.TembaClient.get_contacts')
    def test_sync_with_groups(self, mock_get_contacts, mock_get_groups):
        mock_get_groups.return_value = [TembaGroup.create(uuid='G-101', name="New region", size=2),
                                        TembaGroup.create(uuid='G-102', name="Other region", size=1)]
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='C-101', name="Jan", urns=['tel:123'], groups=['G-101', 'G-005'],
                                fields=dict(chat_name="jan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='C-102', name="Ken", urns=['tel:234'], groups=['G-101', 'G-006'],
                                fields=dict(chat_name="ken"), language='eng', modified_on=timezone.now())
        ]

        # select one new group
        Region.sync_with_groups(self.unicef, ['G-101'])
        self.assertEqual(self.unicef.regions.filter(is_active=True).count(), 1)
        self.assertEqual(self.unicef.regions.filter(is_active=False).count(), 3)  # existing de-activated

        new_region = Region.objects.get(uuid='G-101')
        self.assertEqual(new_region.name, "New region")
        self.assertTrue(new_region.is_active)

        # check contact changes
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        self.assertEqual(self.unicef.contacts.filter(is_active=False).count(), 5)  # existing de-activated

        jan = Contact.objects.get(uuid='C-101')
        self.assertEqual(jan.name, "Jan")
        self.assertEqual(jan.urn, 'tel:123')
        self.assertEqual(jan.region, new_region)
        self.assertTrue(jan.is_active)

        # change group and contacts on chatpro side
        Region.objects.filter(name="New region").update(name="Huh?", is_active=False)
        jan.name = "Janet"
        jan.save()
        Contact.objects.filter(name="Ken").update(is_active=False)

        # re-select new group
        Region.sync_with_groups(self.unicef, ['G-101'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.regions.get(is_active=True).name, 'New region')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(name="Jan", is_active=True)


class GroupTest(TracProTest):
    def test_create(self):
        group = Group.create(self.unicef, "Male Teachers", 'G-101')
        self.assertEqual(group.org, self.unicef)
        self.assertEqual(group.name, "Male Teachers")
        self.assertEqual(group.uuid, 'G-101')

    def test_get_all(self):
        self.assertEqual(len(Group.get_all(self.unicef)), 3)
        self.assertEqual(len(Group.get_all(self.nyaruka)), 1)


class RegionCRUDLTest(TracProTest):
    def test_list(self):
        url = reverse('groups.region_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/region/')

        # log in as an administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

    def test_most_active(self):
        url = reverse('groups.region_most_active')

        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)
        pollrun = PollRun.objects.create(poll=self.poll1, conducted_on=five_weeks_ago)

        # empty response in last month for contact in region #1
        Response.objects.create(flow_run_id=123, pollrun=pollrun, contact=self.contact1,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_EMPTY)

        # partial response not in last month for contact in region #2
        Response.objects.create(flow_run_id=234, pollrun=pollrun, contact=self.contact4,
                                created_on=five_weeks_ago, updated_on=five_weeks_ago, status=RESPONSE_PARTIAL)

        # partial response in last month for contact in region #2
        Response.objects.create(flow_run_id=345, pollrun=pollrun, contact=self.contact4,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_PARTIAL)

        # 2 complete responses in last month for contact in region #3
        Response.objects.create(flow_run_id=456, pollrun=pollrun, contact=self.contact5,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_COMPLETE)
        Response.objects.create(flow_run_id=567, pollrun=pollrun, contact=self.contact5,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.region3.pk)
        self.assertEqual(results[0]['name'], self.region3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.region2.pk)
        self.assertEqual(results[1]['name'], self.region2.name)
        self.assertEqual(results[1]['response_count'], 1)


class GroupCRUDLTest(TracProTest):
    def test_list(self):
        url = reverse('groups.group_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/group/')

        # log in as an administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)

    def test_most_active(self):
        url = reverse('groups.group_most_active')

        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)
        pollrun = PollRun.objects.create(poll=self.poll1, conducted_on=five_weeks_ago)

        # empty response in last month for contact in group #1
        Response.objects.create(flow_run_id=123, pollrun=pollrun, contact=self.contact1,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_EMPTY)

        # partial response not in last month for contact in group #2
        Response.objects.create(flow_run_id=234, pollrun=pollrun, contact=self.contact3,
                                created_on=five_weeks_ago, updated_on=five_weeks_ago, status=RESPONSE_PARTIAL)

        # partial response in last month for contact in group #2
        Response.objects.create(flow_run_id=345, pollrun=pollrun, contact=self.contact3,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_PARTIAL)

        # 2 complete responses in last month for contact in group #3
        Response.objects.create(flow_run_id=456, pollrun=pollrun, contact=self.contact5,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_COMPLETE)
        Response.objects.create(flow_run_id=567, pollrun=pollrun, contact=self.contact5,
                                created_on=five_days_ago, updated_on=five_days_ago, status=RESPONSE_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.group3.pk)
        self.assertEqual(results[0]['name'], self.group3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.group2.pk)
        self.assertEqual(results[1]['name'], self.group2.name)
        self.assertEqual(results[1]['response_count'], 1)


class UserRegionsMiddlewareTest(TracProTest):
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
