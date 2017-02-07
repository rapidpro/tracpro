from __future__ import unicode_literals

from django.utils import timezone

from temba_client.v2.types import Contact as TembaContact

from tracpro.test.cases import TracProTest
from ..utils import intersection, union, filter_dict, temba_compare_contacts, temba_merge_contacts


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