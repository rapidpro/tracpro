from __future__ import absolute_import, unicode_literals

import mock

from temba.types import Contact as TembaContact

from django.test.utils import override_settings
from django.utils import timezone

from tracpro.polls.models import Response
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import Contact


class ContactTest(TracProDataTest):

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    @mock.patch('dash.orgs.models.TembaClient.create_contact')
    def test_create(self, mock_create_contact):
        mock_create_contact.return_value = TembaContact.create(
            uuid='C-007', name="Mo Polls",
            urns=['tel:078123'], groups=['G-001', 'G-005'],
            fields={'facility_code': 'FC234'},
            language='eng', modified_on=timezone.now())

        contact = Contact.create(
            self.unicef, self.user1, "Mo Polls", 'tel:078123',
            self.region1, self.group1, 'FC234', 'eng')

        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(contact.facility_code, 'FC234')
        self.assertEqual(contact.language, 'eng')
        self.assertEqual(contact.created_by, self.user1)
        self.assertIsNotNone(contact.created_on)
        self.assertEqual(contact.modified_by, self.user1)
        self.assertIsNotNone(contact.modified_on)

        # reload and check UUID was updated by push task
        contact = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact.uuid, 'C-007')

        self.assertEqual(mock_create_contact.call_count, 1)

    @mock.patch('dash.orgs.models.TembaClient.get_contact')
    def test_get_or_fetch(self, mock_get_contact):
        mock_get_contact.return_value = TembaContact.create(
            uuid='C-007', name="Mo Polls",
            urns=['tel:078123'], groups=['G-001', 'G-005'],
            fields={'facility_code': 'FC234'},
            language='eng', modified_on=timezone.now())
        # get locally
        contact = Contact.get_or_fetch(self.unicef, 'C-001')
        self.assertEqual(contact.name, "Ann")

        # fetch remotely
        contact = Contact.get_or_fetch(self.unicef, 'C-009')
        self.assertEqual(contact.name, "Mo Polls")

    def test_kwargs_from_temba(self):
        temba_contact = TembaContact.create(
            uuid='C-007', name="Jan", urns=['tel:123'],
            groups=['G-001', 'G-007'],
            fields={'facility_code': 'FC234', 'gender': 'M'},
            language='eng', modified_on=timezone.now())

        kwargs = Contact.kwargs_from_temba(self.unicef, temba_contact)

        self.assertDictEqual(kwargs, {
            'uuid': 'C-007',
            'org': self.unicef,
            'name': "Jan",
            'urn': 'tel:123',
            'region': self.region1,
            'group': self.group3,
            'facility_code': 'FC234',
            'language': 'eng',
        })

        # try creating contact from them
        Contact.objects.create(**kwargs)

    def test_as_temba(self):
        temba_contact = self.contact1.as_temba()
        self.assertEqual(temba_contact.name, "Ann")
        self.assertEqual(temba_contact.urns, ['tel:1234'])
        self.assertEqual(temba_contact.fields, {'facility_code': 'FC123'})
        self.assertEqual(temba_contact.groups, ['G-001', 'G-005'])
        self.assertEqual(temba_contact.uuid, 'C-001')

    def test_get_all(self):
        self.assertEqual(len(Contact.get_all(self.unicef)), 5)
        self.assertEqual(len(Contact.get_all(self.nyaruka)), 1)

    def test_get_responses(self):
        date1 = self.datetime(2014, 1, 1, 7, 0)
        date2 = self.datetime(2014, 1, 1, 8, 0)
        pollrun1 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=date1)
        pollrun1_r1 = factories.Response(
            pollrun=pollrun1, contact=self.contact1,
            created_on=date1, updated_on=date1, status=Response.STATUS_COMPLETE)
        pollrun2 = factories.RegionalPollRun(
            poll=self.poll1, region=self.region1, conducted_on=date2)
        pollrun2_r1 = factories.Response(
            pollrun=pollrun2, contact=self.contact1,
            created_on=date2, updated_on=date2, status=Response.STATUS_EMPTY)

        self.assertEqual(list(self.contact1.get_responses().order_by('pk')),
                         [pollrun1_r1, pollrun2_r1])
        self.assertEqual(list(self.contact1.get_responses(include_empty=False).order_by('pk')),
                         [pollrun1_r1])

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        BROKER_BACKEND='memory',
    )
    @mock.patch('dash.orgs.models.TembaClient.delete_contact')
    def test_release(self, mock_delete_contact):
        self.contact1.release()
        self.assertFalse(self.contact1.is_active)

        self.assertEqual(mock_delete_contact.call_count, 1)

    def test_str(self):
        self.assertEqual(str(self.contact1), "Ann")
        self.contact1.name = ""
        self.contact1.save()
        self.assertEqual(str(self.contact1), "1234")
