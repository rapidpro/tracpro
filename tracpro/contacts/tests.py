from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact
from tracpro.test import TracProTest
from .models import Contact


class ContactTest(TracProTest):
    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.create_contact')
    def test_create(self, mock_create_contact):
        mock_create_contact.return_value = TembaContact.create(uuid='C-007', name="Mo Polls",
                                                               urns=['tel:078123'], groups=['G-001', 'G-005'],
                                                               language='eng', modified_on=timezone.now())

        contact = Contact.create(self.unicef, self.user1, "Mo Polls", 'tel:078123', self.region1, self.group1)

        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.urn, 'tel:078123')
        self.assertEqual(contact.region, self.region1)
        self.assertEqual(contact.created_by, self.user1)
        self.assertIsNotNone(contact.created_on)
        self.assertEqual(contact.modified_by, self.user1)
        self.assertIsNotNone(contact.modified_on)

        # reload and check UUID was updated by push task
        contact = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact.uuid, 'C-007')

        self.assertEqual(mock_create_contact.call_count, 1)

    @patch('dash.orgs.models.TembaClient.get_contact')
    def test_get_or_fetch(self, mock_get_contact):
        mock_get_contact.return_value = TembaContact.create(uuid='C-007', name="Mo Polls",
                                                            urns=['tel:078123'], groups=['G-001', 'G-005'],
                                                            language='eng', modified_on=timezone.now())
        # get locally
        contact = Contact.get_or_fetch(self.unicef, 'C-001')
        self.assertEqual(contact.name, "Ann")

        # fetch remotely
        contact = Contact.get_or_fetch(self.unicef, 'C-009')
        self.assertEqual(contact.name, "Mo Polls")

    def test_kwargs_from_temba(self):
        temba_contact = TembaContact.create(uuid='C-007', name="Jan", urns=['tel:123'],
                                            groups=['G-001', 'G-007'], fields=dict(chat_name="jxn"),
                                            language='eng', modified_on=timezone.now())

        kwargs = Contact.kwargs_from_temba(self.unicef, temba_contact)

        self.assertEqual(kwargs, dict(uuid='C-007', org=self.unicef, name="Jan", urn='tel:123',
                                      region=self.region1, group=self.group3))

        # try creating contact from them
        Contact.objects.create(**kwargs)

    def test_as_temba(self):
        temba_contact = self.contact1.as_temba()
        self.assertEqual(temba_contact.name, "Ann")
        self.assertEqual(temba_contact.urns, ['tel:1234'])
        self.assertEqual(temba_contact.fields, {})
        self.assertEqual(temba_contact.groups, ['G-001', 'G-005'])
        self.assertEqual(temba_contact.uuid, 'C-001')

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.delete_contact')
    def test_release(self, mock_delete_contact):
        self.contact1.release()
        self.assertFalse(self.contact1.is_active)

        self.assertEqual(mock_delete_contact.call_count, 1)

    def test_unicode(self):
        self.assertEqual(unicode(self.contact1), "Ann")
        self.contact1.name = ""
        self.contact1.save()
        self.assertEqual(unicode(self.contact1), "1234")


class ContactCRUDLTest(TracProTest):
    def test_create(self):
        url = reverse('contacts.contact_create')

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'This field is required.')
        self.assertFormError(response, 'form', 'urn', 'This field is required.')
        self.assertFormError(response, 'form', 'region', 'This field is required.')

        # submit again with all fields
        data = dict(name="Mo Polls", urn_0="tel", urn_1="5678", region=self.region1.pk, group=self.group1.pk)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check new contact and profile
        contact = Contact.objects.get(urn='tel:5678')
        self.assertEqual(contact.name, "Mo Polls")
        self.assertEqual(contact.region, self.region1)

        # log in as a user
        self.login(self.user1)

        # try to create contact in region we don't have access to
        data = dict(name="Mo Polls II", urn_0="tel", urn_1="5678", region=self.region3.pk, group=self.group1.pk)
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', 'region',
                             "Select a valid choice. That choice is not one of the available choices.")

        # try again but this time in a region we do have access to
        data = dict(name="Mo Polls II", urn_0="tel", urn_1="5678", region=self.region1.pk, group=self.group1.pk)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

    def test_create_in(self):
        url = reverse('contacts.contact_create_in', args=[self.region1.pk])

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].initial['region'], self.region1)

    def test_update(self):
        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', reverse('contacts.contact_update', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)

        data = dict(name="Morris", urn_0="tel", urn_1="6789", region=self.region2.pk, group=self.group2.pk)
        response = self.url_post('unicef', reverse('contacts.contact_update', args=[self.contact1.pk]), data)
        self.assertEqual(response.status_code, 302)

        # check updated contact and profile
        contact = Contact.objects.get(pk=self.contact1.pk)
        self.assertEqual(contact.name, "Morris")
        self.assertEqual(contact.urn, 'tel:6789')
        self.assertEqual(contact.region, self.region2)
        self.assertEqual(contact.group, self.group2)

    def test_read(self):
        # log in as a user
        self.login(self.user1)

        # view contact in a region we have access to
        response = self.url_get('unicef', reverse('contacts.contact_read', args=[self.contact3.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('contacts.contact_update', args=[self.contact3.pk]))
        self.assertContains(response, "Phone")

        # view contact in a region we don't have access to
        response = self.url_get('unicef', reverse('contacts.contact_read', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['edit_button_url'])
        self.assertContains(response, "Twitter")

        # try to view contact from other org
        response = self.url_get('unicef', reverse('contacts.contact_read', args=[self.contact6.pk]))
        self.assertEqual(response.status_code, 404)

    def test_list(self):
        url = reverse('contacts.contact_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

    def test_filter(self):
        self.login(self.user1)

        # view a region we do have access to
        response = self.url_get('unicef', reverse('contacts.contact_filter', args=[self.region1.pk]))
        self.assertEqual(response.status_code, 200)

        # try to view a region we don't have access to
        response = self.url_get('unicef', reverse('contacts.contact_filter', args=[self.region3.pk]))
        self.assertEqual(response.status_code, 403)

        # try to view a region in a different org
        response = self.url_get('unicef', reverse('contacts.contact_filter', args=[self.region4.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        # log in as an org administrator
        self.login(self.admin)

        # delete contact
        response = self.url_post('unicef', reverse('contacts.contact_delete', args=[self.contact1.pk]))
        self.assertRedirects(response, 'http://unicef.localhost/contact/')
        self.assertFalse(Contact.objects.get(pk=self.contact1.pk).is_active)

        # try to delete contact from other org
        response = self.url_post('unicef', reverse('contacts.contact_delete', args=[self.contact6.pk]))
        self.assertLoginRedirect(response, 'unicef', '/contact/delete/%d/' % self.contact6.pk)
        self.assertTrue(Contact.objects.get(pk=self.contact6.pk).is_active)

        # log in as user
        self.login(self.user1)

        # delete contact from region we have access to
        response = self.url_post('unicef', reverse('contacts.contact_delete', args=[self.contact3.pk]))
        self.assertRedirects(response, 'http://unicef.localhost/contact/')
        contact = Contact.objects.get(pk=self.contact3.pk)
        self.assertFalse(contact.is_active)
        self.assertEqual(contact.modified_by, self.user1)

        # try to delete contact from region we don't have access to
        response = self.url_post('unicef', reverse('contacts.contact_delete', args=[self.contact5.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Contact.objects.get(pk=self.contact5.pk).is_active)
