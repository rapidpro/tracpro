from __future__ import unicode_literals

from django.utils import timezone

from temba_client.v2.types import Contact as TembaContact

from tracpro.test.cases import TracProTest, TracProDataTest
from tracpro.utils import get_uuids
from ..models import Contact
from ..utils import temba_compare_contacts, sync_pull_contacts


class SyncTest(TracProTest):
    def test_temba_compare_contacts(self):
        # no differences
        first = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertIsNone(temba_compare_contacts(first, second))
        self.assertIsNone(temba_compare_contacts(second, first))

        # different name
        second = TembaContact.create(
            uuid='000-001', name="Annie", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'name')

        # different URNs
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234', 'twitter:ann'], groups=['000-001'],
            fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'urns')

        # different group
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-002'],
            fields=dict(chat_name="ann"), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'groups')

        # different field
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="annie"), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'fields')

        # additional field
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="ann", age=18), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'fields')


class SyncPullTest(TracProDataTest):
    def setUp(self):
        super(SyncPullTest, self).setUp()

        self.org = self.unicef
        self.sync_regions = [self.region1, self.region2]
        self.sync_region_names = [self.region1.name, self.region2.name]
        self.sync_groups = [self.group1, self.group2]
        self.sync_group_names = [self.group1.name, self.group2.name]
        self.rapidpro_contacts_as_temba = [
            tracpro_contact.as_temba()
            for tracpro_contact in Contact.objects.filter(
                groups__in=self.sync_groups,
                org=self.org,
            ).distinct()
        ]

        # Add the group_uuid per contact for sync
        contacts = []
        for contact in self.rapidpro_contacts_as_temba:
            for group in contact.groups:
                if group.name in self.sync_group_names or group.name in self.sync_region_names:
                    contacts.append(contact)

        self.rapidpro_contacts_as_temba = contacts

        # Contacts that we are actually syncing here, because they are in the regions we sync
        self.sync_contacts = Contact.objects.filter(region__in=(self.sync_regions))
        # Order this list
        self.sync_contacts = list(set([contact.uuid for contact in self.sync_contacts]))
        self.deleted_rapidpro_contacts = []

        def mock_get_contacts_in_groups(groups, deleted=None):
            if deleted:
                return self.deleted_rapidpro_contacts
            else:
                return self.rapidpro_contacts_as_temba

        self.mock_temba_client.get_contacts_in_groups = mock_get_contacts_in_groups

    def get_region_uuids(self):
        return set(get_uuids(self.sync_regions))

    def get_group_uuids(self):
        return set(get_uuids(self.sync_groups))

    def test_no_change(self):
        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )

        # Most tuples don't change
        # because we just returned the contacts we already had
        # However, we always update the contacts to get most up-to-date information
        # on the region/cohort relationship

        self.assertTupleEqual(([], self.sync_contacts, [], []), (created, updated, deleted, failed))
        self.assertFalse(errors)

    def test_new_contact_in_rapidpro(self):
        original_kwargs = self.contact1.as_temba().serialize()
        new_temba_contact = self.contact1.as_temba()

        # Work around the overloaded 'delete' method on Contact to really delete contact1 locally,
        # so as far as our code is concerned, contact1 will be a new contact when we
        # see it come back from Rapidpro.
        Contact.objects.filter(uuid=self.contact1.uuid).delete()

        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )

        #
        updated_contacts = [c for c in self.sync_contacts if c != new_temba_contact.uuid]
        self.assertTupleEqual(
            ([new_temba_contact.uuid], updated_contacts, [], []),
            (created, updated, deleted, failed))

        # We have created a new contact:
        c = Contact.objects.get(uuid=new_temba_contact.uuid)
        # and it has the expected data:
        new_kwargs = c.as_temba().serialize()
        del original_kwargs['modified_on']
        del new_kwargs['modified_on']
        self.assertEqual(original_kwargs['uuid'], new_kwargs['uuid'])
        self.assertEqual(original_kwargs['language'], new_kwargs['language'])
        self.assertEqual(original_kwargs['fields'], new_kwargs['fields'])
        self.assertEqual(original_kwargs['created_on'], new_kwargs['created_on'])
        self.assertEqual(original_kwargs['name'], new_kwargs['name'])
        self.assertEqual(original_kwargs['urns'], new_kwargs['urns'])
        original_group_uuids = [grp['uuid'] for grp in original_kwargs['groups']]
        new_group_uuids = [grp['uuid'] for grp in new_kwargs['groups']]
        self.assertEqual(set(original_group_uuids), set(new_group_uuids))

    def test_new_contact_with_no_urns(self):
        # Work around the overloaded 'delete' method on Contact to really delete contact1 locally,
        # so as far as our code is concerned, this will be a new contact when we
        # see it come back from Rapidpro.
        uuid_to_delete = self.rapidpro_contacts_as_temba[0].uuid
        Contact.objects.filter(uuid=uuid_to_delete).delete()
        self.sync_contacts.remove(uuid_to_delete)

        # Remove the urns from that contact as we'll see it from rapidpro
        self.rapidpro_contacts_as_temba[0].urns = []

        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )
        # We do *not* see the new contact (or blow up)
        self.assertTupleEqual(([], self.sync_contacts, [], []), (created, updated, deleted, failed))
        self.assertFalse(errors)

    def test_modified_contact_in_rapidpro(self):
        # Have "rapidpro" return a new name on the first contact in the list
        new_name = "Mr. McGillicuddy"
        modified = self.rapidpro_contacts_as_temba[0]
        modified.name = new_name

        existing_contact = Contact.objects.get(uuid=modified.uuid)

        # Sync and see what happens
        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], self.sync_contacts, [], []),
                              (created, updated, deleted, failed))
        # Our contact has changed its name, in the existing record
        c = Contact.objects.get(uuid=self.rapidpro_contacts_as_temba[0].uuid)
        self.assertEqual(c.pk, existing_contact.pk)
        self.assertEqual(c.name, new_name)
        self.assertFalse(errors)

    def test_deleted_contact_in_rapidpro(self):
        deleted_rapidpro_contact = self.rapidpro_contacts_as_temba.pop()
        self.deleted_rapidpro_contacts.append(deleted_rapidpro_contact)
        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], self.sync_contacts, [deleted_rapidpro_contact.uuid], []),
                              (created, updated, deleted, failed))
        # Our contact has changed to is_active=False
        c = Contact.objects.get(uuid=deleted_rapidpro_contact.uuid)
        self.assertFalse(c.is_active)
        self.assertFalse(errors)

    def test_blocked_contact_in_rapidpro(self):
        blocked_contact = self.rapidpro_contacts_as_temba[0]
        blocked_contact.blocked = True
        self.sync_contacts.remove(blocked_contact.uuid)
        created, updated, deleted, failed, errors = sync_pull_contacts(
            org=self.org,
            region_uuids=self.get_region_uuids(),
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], self.sync_contacts, [blocked_contact.uuid], []),
                              (created, updated, deleted, failed))
        # Our contact has changed to is_active=False
        c = Contact.objects.get(uuid=blocked_contact.uuid)
        self.assertFalse(c.is_active)
        self.assertFalse(errors)
