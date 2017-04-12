from __future__ import unicode_literals

from django.db.models import Q
from django.utils import timezone

from temba_client.v2.types import Contact as TembaContact

from tracpro.test.cases import TracProTest, TracProDataTest
from tracpro.utils import get_uuids
from ..models import Contact
from ..utils import intersection, union, filter_dict, temba_compare_contacts, temba_merge_contacts, \
    sync_pull_contacts


class InitTest(TracProTest):
    def test_intersection(self):
        self.assertEqual(intersection(), [])
        self.assertEqual(intersection([1]), [1])
        self.assertEqual(intersection([2, 1, 1]), [2, 1])
        self.assertEqual(intersection([3, 2, 1], [2, 3, 4]), [3, 2])  # order from first list
        self.assertEqual(intersection([4, 3, 2, 1], [3, 2, 4], [1, 2, 3]), [3, 2])

    def test_union(self):
        self.assertEqual(union(), [])
        self.assertEqual(union([1]), [1])
        self.assertEqual(union([2, 1, 1], [1, 2, 3]), [2, 1, 3])  # order is first seen
        self.assertEqual(union([2, 1], [2, 3, 3], [4, 5]), [2, 1, 3, 4, 5])

    def test_filter_dict(self):
        d = {'a': 123, 'b': 'xyz', 'c': 456}
        self.assertEqual(filter_dict(d, ()), {})
        self.assertEqual(filter_dict(d, ('a', 'c')), {'a': 123, 'c': 456})


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
        self.assertEqual(temba_compare_contacts(first, second, groups=('000-001', '000-002')),
                         'groups')
        self.assertIsNone(temba_compare_contacts(first, second, groups=()))
        self.assertIsNone(temba_compare_contacts(first, second, groups=('000-003', '000-004')))

        # different field
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="annie"), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'fields')
        self.assertEqual(temba_compare_contacts(first, second, fields=('chat_name', 'gender')),
                         'fields')
        self.assertIsNone(temba_compare_contacts(first, second, fields=()))
        self.assertIsNone(temba_compare_contacts(first, second, fields=('age', 'gender')))

        # additional field
        second = TembaContact.create(
            uuid='000-001', name="Ann", urns=['tel:1234'], groups=['000-001'],
            fields=dict(chat_name="ann", age=18), language='eng', modified_on=timezone.now())
        self.assertEqual(temba_compare_contacts(first, second), 'fields')
        self.assertIsNone(temba_compare_contacts(first, second, fields=()))
        self.assertIsNone(temba_compare_contacts(first, second, fields=('chat_name',)))

    def test_temba_merge_contacts(self):
        contact1 = TembaContact.create(uuid="000-001", name="Bob",
                                       urns=['tel:123', 'email:bob@bob.com'],
                                       fields=dict(chat_name="bob", age=23),
                                       groups=['000-001', '000-002', '000-010'])
        contact2 = TembaContact.create(uuid="000-001", name="Bobby",
                                       urns=['tel:234', 'twitter:bob'],
                                       fields=dict(chat_name="bobz", state='IN'),
                                       groups=['000-003', '000-009', '000-011'])

        merged = temba_merge_contacts(contact1, contact2, mutex_group_sets=(
            ('000-001', '000-002', '000-003'),
            ('000-008', '000-009'),
            ('000-098', '000-099'),
        ))
        self.assertEqual(merged.uuid, '000-001')
        self.assertEqual(merged.name, "Bob")
        self.assertEqual(sorted(merged.urns), ['email:bob@bob.com', 'tel:123', 'twitter:bob'])
        self.assertEqual(merged.fields, dict(chat_name="bob", age=23, state='IN'))
        self.assertEqual(sorted(merged.groups), ['000-001', '000-009', '000-010', '000-011'])


class SyncPullTest(TracProDataTest):
    def setUp(self):
        super(SyncPullTest, self).setUp()

        self.org = self.unicef
        self.sync_regions = [self.region1, self.region2]
        self.sync_groups = [self.group1, self.group2]
        self.rapidpro_contacts_as_temba = [
            tracpro_contact.as_temba()
            for tracpro_contact in Contact.objects.filter(
                Q(groups__in=self.sync_groups),
                org=self.org,
            ).distinct()
        ]
        self.deleted_rapidpro_contacts = []

        def mock_get_contacts_in_groups(groups, deleted=None):
            if deleted:
                return self.deleted_rapidpro_contacts
            else:
                return self.rapidpro_contacts_as_temba

        self.mock_temba_client.get_contacts_in_groups = mock_get_contacts_in_groups

    def get_group_uuids(self):
        return set(get_uuids(self.sync_regions) + get_uuids(self.sync_groups))

    def test_no_change(self):
        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )

        # Should be no change since we just returned the contacts we already had
        self.assertTupleEqual(([], [], [], []), (created, updated, deleted, failed))

    def test_new_contact_in_rapidpro(self):
        original_kwargs = self.contact1.as_temba().serialize()
        new_temba_contact = self.contact1.as_temba()

        # Work around the overloaded 'delete' method on Contact to really delete contact1 locally,
        # so as far as our code is concerned, contact1 will be a new contact when we
        # see it come back from Rapidpro.
        Contact.objects.filter(uuid=self.contact1.uuid).delete()

        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([new_temba_contact.uuid], [], [], []), (created, updated, deleted, failed))

        # We have created a new contact:
        c = Contact.objects.get(uuid=new_temba_contact.uuid)
        # and it has the expected data:
        new_kwargs = c.as_temba().serialize()
        del original_kwargs['modified_on']
        del new_kwargs['modified_on']
        self.assertDictEqual(original_kwargs, new_kwargs)

    def test_new_contact_with_no_urns(self):
        # Work around the overloaded 'delete' method on Contact to really delete contact1 locally,
        # so as far as our code is concerned, this will be a new contact when we
        # see it come back from Rapidpro.
        Contact.objects.filter(uuid=self.rapidpro_contacts_as_temba[0].uuid).delete()

        # Remove the urns from that contact as we'll see it from rapidpro
        self.rapidpro_contacts_as_temba[0].urns = []

        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )
        # We do *not* see the new contact (or blow up)
        self.assertTupleEqual(([], [], [], []), (created, updated, deleted, failed))

    def test_modified_contact_in_rapidpro(self):
        # Have "rapidpro" return a new name on the first contact in the list
        new_name = "Mr. McGillicuddy"
        modified = self.rapidpro_contacts_as_temba[0]
        modified.name = new_name

        existing_contact = Contact.objects.get(uuid=modified.uuid)

        # Sync and see what happens
        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], [self.rapidpro_contacts_as_temba[0].uuid], [], []),
                              (created, updated, deleted, failed))
        # Our contact has changed its name, in the existing record
        c = Contact.objects.get(uuid=self.rapidpro_contacts_as_temba[0].uuid)
        self.assertEqual(c.pk, existing_contact.pk)
        self.assertEqual(c.name, new_name)

    def test_deleted_contact_in_rapidpro(self):
        deleted_rapidpro_contact = self.rapidpro_contacts_as_temba.pop()
        self.deleted_rapidpro_contacts.append(deleted_rapidpro_contact)
        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], [], [deleted_rapidpro_contact.uuid], []),
                              (created, updated, deleted, failed))
        # Our contact has changed to is_active=False
        c = Contact.objects.get(uuid=deleted_rapidpro_contact.uuid)
        self.assertFalse(c.is_active)

    def test_blocked_contact_in_rapidpro(self):
        blocked_contact = self.rapidpro_contacts_as_temba[0]
        blocked_contact.blocked = True
        created, updated, deleted, failed = sync_pull_contacts(
            org=self.org,
            group_uuids=self.get_group_uuids(),
        )
        self.assertTupleEqual(([], [], [blocked_contact.uuid], []),
                              (created, updated, deleted, failed))
        # Our contact has changed to is_active=False
        c = Contact.objects.get(uuid=blocked_contact.uuid)
        self.assertFalse(c.is_active)
