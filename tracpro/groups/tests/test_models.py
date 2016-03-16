from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test.utils import override_settings

from temba_client.types import Group as TembaGroup

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest, TracProTest

from .. import models


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    BROKER_BACKEND='memory',
)
class TestRegion(TracProTest):

    def setUp(self):
        super(TestRegion, self).setUp()

        self.org = factories.Org()

        self.temba_groups = {
            '1': TembaGroup.create(uuid="1", name="Uganda"),
            '2': TembaGroup.create(uuid="2", name="Kampala"),
            '3': TembaGroup.create(uuid="3", name="Entebbe"),
            '4': TembaGroup.create(uuid="4", name="Makerere"),
        }

        self.uganda = factories.Region(
            org=self.org, uuid='1', name="Uganda")
        self.kampala = factories.Region(
            org=self.org, uuid='2', name="Kampala", parent=self.uganda)
        self.entebbe = factories.Region(
            org=self.org, uuid='3', name="Entebbe", parent=self.uganda)
        self.makerere = factories.Region(
            org=self.org, uuid='4', name="makerere", parent=self.kampala)
        self.inactive = factories.Region(
            org=self.org, uuid='5', name="inactive", parent=self.kampala,
            is_active=False)

        self.mock_temba_client.get_contacts.return_value = []

    def refresh_regions(self):
        """Refresh all regions from the database."""
        for region in (self.uganda, self.kampala, self.entebbe, self.makerere,
                       self.inactive):
            region = region.refresh_from_db()

    def test_create(self):
        """The create() method is a shortcut for creating a new Region."""
        region = models.Region.objects.create(org=self.org, name="Zabul", uuid="G-101")
        contact = factories.Contact(org=self.org, region=region)
        user = User.create(
            self.org, "User", "user@unicef.org", "pass", False, [region])

        self.assertEqual(region.org, self.org)
        self.assertEqual(region.name, "Zabul")
        self.assertEqual(region.uuid, 'G-101')
        self.assertEqual(list(region.get_contacts()), [contact])
        self.assertEqual(list(region.get_users()), [user])

    def test_get_all(self):
        """Return all active regions for the organization."""
        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.entebbe,
            self.makerere,
        ]))

    def test_deactivate_no_children(self):
        """Deactivation workflow when region has no children."""
        self.makerere.deactivate()
        self.refresh_regions()

        self.assertFalse(self.makerere.is_active)
        self.assertIsNone(self.makerere.parent)
        self.assertEqual(list(self.makerere.children.all()), [])

    def test_deactivate_with_children(self):
        """Deactivation workflow when region has children."""
        self.kampala.deactivate()
        self.refresh_regions()

        self.assertFalse(self.kampala.is_active)
        self.assertIsNone(self.kampala.parent)
        self.assertEqual(list(self.kampala.children.all()), [])
        self.assertEqual(self.makerere.parent, self.uganda)
        self.assertEqual(self.inactive.parent, self.uganda)

    def test_deactivate_top_level(self):
        """Deactivation workflow for top-level region."""
        self.uganda.deactivate()
        self.refresh_regions()

        self.assertFalse(self.uganda.is_active)
        self.assertIsNone(self.uganda.parent)
        self.assertEqual(list(self.uganda.children.all()), [])
        self.assertIsNone(self.kampala.parent)
        self.assertIsNone(self.entebbe.parent)
        self.assertEqual(self.makerere.parent, self.kampala)
        self.assertEqual(self.inactive.parent, self.kampala)

    def test_sync_deactivate(self):
        """Deactivate any group whose UUID is not given."""
        self.mock_temba_client.get_groups.return_value = self.temba_groups.values()
        uuids = ['1', '2', '4']  # no Entebbe
        models.Region.sync_with_temba(self.org, uuids)
        self.refresh_regions()

        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.makerere,
        ]))
        self.assertEqual(self.mock_temba_client.get_groups.call_count, 1)
        self.assertEqual(self.mock_temba_client.get_contacts.call_count, 2)

    def test_sync_update_existing(self):
        """Update existing group with new information from remote."""
        self.temba_groups['2'].name = "Changed"  # Kampala
        self.mock_temba_client.get_groups.return_value = self.temba_groups.values()
        uuids = ['1', '2', '3', '4']
        models.Region.sync_with_temba(self.org, uuids)
        self.refresh_regions()

        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.makerere,
            self.entebbe,
        ]))
        self.assertEqual(self.kampala.name, "Changed")
        self.assertEqual(self.kampala.parent, self.uganda)
        self.assertEqual(self.mock_temba_client.get_groups.call_count, 1)
        self.assertEqual(self.mock_temba_client.get_contacts.call_count, 2)

    def test_sync_reactivate(self):
        """Reactivate a group that existed previously."""
        self.mock_temba_client.get_groups.return_value = self.temba_groups.values()
        self.entebbe.deactivate()
        uuids = ['1', '2', '3', '4']
        models.Region.sync_with_temba(self.org, uuids)
        self.refresh_regions()

        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.makerere,
            self.entebbe,
        ]))
        self.assertTrue(self.entebbe.is_active)
        self.assertEqual(self.entebbe.name, "Entebbe")
        self.assertEqual(self.entebbe.parent, None)
        self.assertEqual(self.mock_temba_client.get_groups.call_count, 1)
        self.assertEqual(self.mock_temba_client.get_contacts.call_count, 2)

    def test_sync_create_new(self):
        """Create a new group if the UUID hasn't been seen before."""
        self.temba_groups['6'] = TembaGroup.create(uuid='6', name="New")
        self.mock_temba_client.get_groups.return_value = self.temba_groups.values()
        uuids = ['1', '2', '3', '4', '6']
        models.Region.sync_with_temba(self.org, uuids)
        self.refresh_regions()

        new_region = models.Region.objects.get(uuid='6')
        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.makerere,
            self.entebbe,
            new_region,
        ]))
        self.assertEqual(new_region.name, "New")
        self.assertIsNone(new_region.parent, None)
        self.assertEqual(self.mock_temba_client.get_groups.call_count, 1)
        self.assertEqual(self.mock_temba_client.get_contacts.call_count, 2)

    def test_sync_removed_remote(self):
        """Deactivate a group locally if it has been removed from the remote."""
        self.temba_groups.pop('3')  # Entebbe
        self.mock_temba_client.get_groups.return_value = self.temba_groups.values()
        uuids = ['1', '2', '3', '4']
        models.Region.sync_with_temba(self.org, uuids)
        self.refresh_regions()

        self.assertFalse(self.entebbe.is_active)
        self.assertIsNone(self.entebbe.parent)
        self.assertEqual(set(models.Region.get_all(self.org)), set([
            self.uganda,
            self.kampala,
            self.makerere,
        ]))
        self.assertEqual(self.mock_temba_client.get_groups.call_count, 1)
        self.assertEqual(self.mock_temba_client.get_contacts.call_count, 2)


class TestGroup(TracProDataTest):

    def test_create(self):
        group = models.Group.objects.create(
            org=self.unicef, name="Male Teachers", uuid='G-101')
        self.assertEqual(group.org, self.unicef)
        self.assertEqual(group.name, "Male Teachers")
        self.assertEqual(group.uuid, 'G-101')

    def test_get_all(self):
        self.assertEqual(len(models.Group.get_all(self.unicef)), 3)
        self.assertEqual(len(models.Group.get_all(self.nyaruka)), 1)
