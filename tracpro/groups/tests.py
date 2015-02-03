from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup
from tracpro.contacts.models import Contact
from tracpro.groups.models import Region, Group
from tracpro.test import TracProTest


class RegionTest(TracProTest):
    def test_create(self):
        zabul = Region.create(self.unicef, "Zabul", 'G-101')
        jan = Contact.create(self.unicef, self.admin, "Jan", 'tel:1234', zabul, self.group1, 'C-101')
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
        mock_get_groups.return_value = [TembaGroup.create(uuid='G-101', name="New region", size=2)]
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
        list_url = reverse('groups.region_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/region/')

        # log in as an administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)


class UserRegionsMiddlewareTest(TracProTest):
    def test_process_request(self):
        # make anonymous request to home page
        response = self.url_get('unicef', reverse('home.home'))
        self.assertEqual(response.status_code, 302)

        self.login(self.user2)

        # should default to first user region A-Z
        response = self.url_get('unicef', reverse('home.home'))
        self.assertContains(response, "Khost", status_code=200)

        # should come from session this time
        response = self.url_get('unicef', reverse('home.home'))
        self.assertContains(response, "Khost", status_code=200)

        # any page allows region to be set via _region param
        response = self.url_get('unicef', reverse('home.home'), {'_region': self.region3.pk})
        self.assertContains(response, "Kunar", status_code=200)

        # can't set to region that user doesn't have access to
        response = self.url_get('unicef', reverse('home.home'), {'_region': self.region1.pk})
        self.assertContains(response, "Khost", status_code=200)
