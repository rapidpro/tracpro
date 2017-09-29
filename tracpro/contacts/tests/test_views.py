from __future__ import unicode_literals

import datetime
import json
import pytz

from unittest import skip

from temba_client.v2.types import Contact as TembaContact, Run

from django.core.urlresolvers import reverse
from django.utils import timezone

from tracpro.polls.models import Response
from tracpro.test import factories
from tracpro.test.cases import TracProDataTest

from ..models import Contact


class ContactCRUDLTest(TracProDataTest):

    def test_create(self):
        url = reverse('contacts.contact_create')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(len(form.errors), 4, form.errors)
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        self.assertFormError(response, 'form', 'urn', 'This field is required.')
        self.assertFormError(response, 'form', 'region', 'This field is required.')
        self.assertFormError(response, 'form', 'groups', 'This field is required.')

        # submit again with all fields
        temba_contact = TembaContact()
        temba_contact.uuid = "uuid"
        self.mock_temba_client.create_contact.return_value = temba_contact
        response = self.url_post('unicef', url, {
            'name': "Mo Polls",
            'urn_0': "tel",
            'urn_1': "+16782345765",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
            'language': 'eng',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.mock_temba_client.create_contact.call_count, 1)

        # check new contact and profile
        contact = Contact.objects.get(urn='tel:+16782345765')
        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(set(contact.groups.all()), set([self.group1, self.group2, self.group3]))
        self.assertEqual(contact.language, 'eng')

        # log in as a user
        self.login(self.user1)

        # try to create contact in region we don't have access to
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+16782345765",
            'region': self.region3.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
        })

        self.assertFormError(response, 'form', 'region',
                             "Select a valid choice. That choice is not one "
                             "of the available choices.")

    @skip("Skipping test_create_with_access() for now.")
    def test_create_with_access(self):
        url = reverse('contacts.contact_create')

        # log in as a user
        self.login(self.user1)

        # try again but this time in a region we do have access to
        response = self.url_post('unicef', url, {
            'name': "Mo Polls II",
            'urn_0': "tel",
            'urn_1': "+16782345765",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk, self.group3.pk),
        })

        self.assertEqual(response.status_code, 302)

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

    def test_update(self):
        # log in as a user
        self.login(self.user1)
        url = reverse('contacts.contact_update', args=[self.contact1.pk])

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        response = self.url_post('unicef', url, {
            'name': "Morris",
            'urn_0': "tel",
            'urn_1': "+16782345765",
            'region': self.region1.pk,
            'groups': (self.group1.pk, self.group2.pk),
            'language': 'kin',
        })

        self.assertEqual(response.status_code, 302)

        # check updated contact and profile
        contact = Contact.objects.get(pk=self.contact1.pk)
        self.assertEqual(contact.name, "Morris")
        self.assertEqual(contact.urn, 'tel:+16782345765')
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
