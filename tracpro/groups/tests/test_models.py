import mock

from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.utils import timezone

from temba.types import Contact as TembaContact, Group as TembaGroup

from tracpro.contacts.models import Contact
from tracpro.test import TracProTest

from .. import models


class TestRegion(TracProTest):

    def test_create(self):
        zabul = models.Region.create(self.unicef, "Zabul", 'G-101')
        jan = self.create_contact(
            self.unicef, "Jan", 'tel:1234', zabul, self.group1, 'C-101')
        bob = User.create(
            self.unicef, "Bob", "bob@unicef.org", "pass", False, [zabul])

        self.assertEqual(zabul.org, self.unicef)
        self.assertEqual(zabul.name, "Zabul")
        self.assertEqual(zabul.uuid, 'G-101')
        self.assertEqual(list(zabul.get_contacts()), [jan])
        self.assertEqual(list(zabul.get_users()), [bob])

    def test_get_all(self):
        self.assertEqual(len(models.Region.get_all(self.unicef)), 3)
        self.assertEqual(len(models.Region.get_all(self.nyaruka)), 1)

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    @mock.patch('dash.orgs.models.TembaClient.get_groups')
    @mock.patch('dash.orgs.models.TembaClient.get_contacts')
    def test_sync_with_groups(self, mock_get_contacts, mock_get_groups):
        mock_get_groups.return_value = [
            TembaGroup.create(
                uuid='G-101',
                name="New region",
                size=2,
            ),
            TembaGroup.create(
                uuid='G-102',
                name="Other region",
                size=1,
            ),
        ]
        mock_get_contacts.return_value = [
            TembaContact.create(
                uuid='C-101',
                name="Jan",
                urns=['tel:123'],
                groups=['G-101', 'G-005'],
                fields={
                    'chat_name': "jan",
                    'language': 'eng',
                    'modified_on': timezone.now(),
                },
            ),
            TembaContact.create(
                uuid='C-102',
                name="Ken",
                urns=['tel:234'],
                groups=['G-101', 'G-006'],
                fields={
                    'chat_name': "ken",
                    'language': 'eng',
                    'modified_on': timezone.now(),
                }
            ),
        ]

        # select one new group
        models.Region.sync_with_groups(self.unicef, ['G-101'])
        self.assertEqual(self.unicef.regions.filter(is_active=True).count(), 1)
        # existing de-activated
        self.assertEqual(self.unicef.regions.filter(is_active=False).count(), 3)

        new_region = models.Region.objects.get(uuid='G-101')
        self.assertEqual(new_region.name, "New region")
        self.assertTrue(new_region.is_active)

        # check contact changes
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        # existing de-activated
        self.assertEqual(self.unicef.contacts.filter(is_active=False).count(), 5)

        jan = Contact.objects.get(uuid='C-101')
        self.assertEqual(jan.name, "Jan")
        self.assertEqual(jan.urn, 'tel:123')
        self.assertEqual(jan.region, new_region)
        self.assertTrue(jan.is_active)

        # change group and contacts on chatpro side
        models.Region.objects.filter(name="New region").update(name="Huh?", is_active=False)
        jan.name = "Janet"
        jan.save()
        Contact.objects.filter(name="Ken").update(is_active=False)

        # re-select new group
        models.Region.sync_with_groups(self.unicef, ['G-101'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.regions.get(is_active=True).name, 'New region')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(name="Jan", is_active=True)


class TestGroup(TracProTest):

    def test_create(self):
        group = models.Group.create(self.unicef, "Male Teachers", 'G-101')
        self.assertEqual(group.org, self.unicef)
        self.assertEqual(group.name, "Male Teachers")
        self.assertEqual(group.uuid, 'G-101')

    def test_get_all(self):
        self.assertEqual(len(models.Group.get_all(self.unicef)), 3)
        self.assertEqual(len(models.Group.get_all(self.nyaruka)), 1)
