from __future__ import unicode_literals

import datetime
import json
import pytz

from temba_client.v2.types import Contact as TembaContact, Run

from django.core.urlresolvers import reverse
from django.utils import timezone

from tracpro.polls.models import Response
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import Contact


class ContactCRUDLTest(TracProDataTest):

    def test_create_no_fields(self):
        url = reverse('contacts.contact_create')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 5, form.errors)
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        self.assertFormError(response, 'form', 'urn', 'This field is required.')
        self.assertFormError(response, 'form', 'region', 'This field is required.')
        self.assertFormError(response, 'form', 'groups', 'This field is required.')
        self.assertFormError(response, 'form', 'language', 'This field is required.')

    def test_create_with_fields(self):
        url = reverse('contacts.contact_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit again with all fields
        temba_contact = TembaContact()
        temba_contact.uuid = "uuid"
        self.mock_temba_client.create_contact.return_value = temba_contact
        self.mock_temba_client.get_contacts.return_value = []
        response = self.url_post('unicef', url, {
            'name': "Mo Polls",
            'urn_0': "tel",
            'urn_1': "+19102223333",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_temba_client.create_contact.call_count, 1)

        # check new contact and profile
        contact = Contact.objects.get(urn='tel:+19102223333')
        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(set(contact.groups.all()), set([self.group1, self.group2, self.group3]))
        self.assertEqual(contact.language, 'eng')

    def test_create_without_access(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # try to create contact in region we don't have access to
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+16782345765",
            'region': self.region3.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertFormError(response, 'form', 'region',
                             "Select a valid choice. That choice is not one "
                             "of the available choices.")

        # test ajax querying for languages
        response = self.url_get('unicef', '%s?initial=' % url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), dict(results=[]))
        response = self.url_get('unicef', '%s?initial=eng' % url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content),
                         dict(results=[dict(id='eng', text='English')]))

        response = self.url_get('unicef', '%s?search=' % url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)['results']), 10)
        response = self.url_get('unicef', '%s?search=Kin' % url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content),
                         dict(results=[dict(id='kin', text='Kinyarwanda')]))

    def test_create_with_access(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        temba_contact = TembaContact()
        temba_contact.uuid = "uuid"
        self.mock_temba_client.create_contact.return_value = temba_contact
        self.mock_temba_client.get_contacts.return_value = []

        # try again but this time in a region we do have access to
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+16782345763",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 302)

    def test_create_invalid_phone_number(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # phone number is not numeric
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "qwerty",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', (
                                                        'This is not a valid phone number.  '
                                                        'A valid phone number must include "+" and country '
                                                        'code / region (e.g. "+1" for North America).'))

    def test_create_invalid_country_code(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # phone number does not have country code
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "2345263746",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', ('This phone number has an invalid country code.'))

    def test_create_short_phone_number(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # phone number is too short
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+167",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', ('The string supplied is too short to be a phone number.'))

    def test_create_long_phone_number(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # phone number is too long
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+167823457657364576297",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', ('The string supplied is too long to be a phone number.'))

    def test_create_urn_already_used(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        contact = Contact.objects.get(pk=self.contact1.pk)
        temba_contact = contact.as_temba()
        temba_contact.urns = ["tel:+19102223333"]
        self.mock_temba_client.create_contact.return_value = temba_contact
        self.mock_temba_client.get_contacts.return_value = [self.mock_temba_client.create_contact.return_value]

        # phone number has already been used
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+19102223333",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', ('This phone number is already being used by another contact.'))

    def test_create_invalid_twitter_handle(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # try again using an invalid Twitter Handle
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "twitter",
            'urn_1': "88-uu-oo",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', (
                                                        'This is not a valid Twitter handle.  '
                                                        'A valid handle has only letters A-Z, '
                                                        'numbers 0-9, and underscores (_), '
                                                        'and has up to 15 characters.'
                                                        ))

    def test_create_invalid_twitter_id(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # try again using an invalid Twitter ID
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "twitterid",
            'urn_1': "just_a_handle",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', (
                                                        'This is not a valid numeric ID.  '
                                                        'The correct format is: <numeric id>#<Twitter handle>'
                                                        ))

    def test_create_invalid_numeric_id(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # try again using an invalid Twitter numeric ID
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "twitterid",
            'urn_1': "aaa123#handle",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertFormError(response, 'form', 'urn', (
                                                        'This is not a valid numeric ID.  '
                                                        'A valid numeric ID has only numbers 0-9.'
                                                        ))

    def test_update(self):
        # log in as a user
        self.login(self.user1)
        url = reverse('contacts.contact_update', args=[self.contact1.pk])

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        contact = Contact.objects.get(pk=self.contact1.pk)
        temba_contact = contact.as_temba()
        self.mock_temba_client.create_contact.return_value = temba_contact
        self.mock_temba_client.get_contacts.return_value = [self.mock_temba_client.create_contact.return_value]

        response = self.url_post('unicef', url, {
            'name': "Morris",
            'urn_0': "tel",
            'urn_1': "+16782345721",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk),
            'language': 'kin',
        })

        self.assertEqual(response.status_code, 302)

        # check updated contact and profile
        contact = Contact.objects.get(pk=self.contact1.pk)
        self.assertEqual(contact.name, "Morris")
        self.assertEqual(contact.urn, 'tel:+16782345721')
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(set(contact.groups.all()), set((self.group1, self.group2)))
        self.assertEqual(contact.language, 'kin')

        # try to update contact in a region we don't have access to
        response = self.url_get(
            'unicef', reverse('contacts.contact_read', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 404)

        # try to update contact from other org
        response = self.url_get(
            'unicef', reverse('contacts.contact_read', args=[self.contact6.pk]))
        self.assertEqual(response.status_code, 404)

    def test_read(self):
        # log in as a user
        self.login(self.user1)

        # view contact in a region we have access to
        response = self.url_get(
            'unicef', reverse('contacts.contact_read', args=[self.contact2.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phone")

        # try to view contact in a region we don't have access to
        response = self.url_get(
            'unicef', reverse('contacts.contact_read', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 404)

        # try to view contact from other org
        response = self.url_get(
            'unicef', reverse('contacts.contact_read', args=[self.contact6.pk]))
        self.assertEqual(response.status_code, 404)

    def test_list(self):
        pollrun1 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=datetime.datetime(2014, 12, 1, tzinfo=pytz.UTC))
        Response.create_empty(
            self.unicef, pollrun1,
            Run.create(id=123, contact='C-001', created_on=timezone.now()))

        self.login(self.admin)
        response = self.url_get('unicef', reverse('contacts.contact_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)
        # no poll pollruns shown in "All Regions" view
        self.assertNotContains(response, "Farm Poll")

        url = '{}?search=an'.format(reverse('contacts.contact_list'))
        response = self.url_get('unicef', url)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertContains(response, "Ann")
        self.assertContains(response, "Dan")

        self.login(self.user1)

        response = self.url_get('unicef', reverse('contacts.contact_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertContains(response, "Farm Poll")

    def test_delete(self):
        # log in as an org administrator
        self.login(self.admin)

        # delete contact
        response = self.url_post(
            'unicef', reverse('contacts.contact_delete', args=[self.contact1.pk]))
        self.assertRedirects(
            response, 'http://unicef.testserver/contact/', fetch_redirect_response=False)
        self.assertFalse(Contact.objects.get(pk=self.contact1.pk).is_active)

        # try to delete contact from other org
        response = self.url_post(
            'unicef', reverse('contacts.contact_delete', args=[self.contact6.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Contact.objects.get(pk=self.contact6.pk).is_active)

        # log in as user
        self.login(self.user1)

        # delete contact from region we have access to
        response = self.url_post(
            'unicef', reverse('contacts.contact_delete', args=[self.contact2.pk]))
        self.assertRedirects(
            response, 'http://unicef.testserver/contact/', fetch_redirect_response=False)
        contact = Contact.objects.get(pk=self.contact2.pk)
        self.assertFalse(contact.is_active)
        self.assertEqual(contact.modified_by, self.user1)

        # try to delete contact from region we don't have access to
        response = self.url_post(
            'unicef', reverse('contacts.contact_delete', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Contact.objects.get(pk=self.contact5.pk).is_active)
