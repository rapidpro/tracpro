from __future__ import unicode_literals

import mock

from django.core.exceptions import NON_FIELD_ERRORS
from django.test import TestCase
from django.test import override_settings

from tracpro.orgs_ext.forms import FetchRunsForm
from tracpro.polls.models import SAMEDAY_LAST
from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import forms


@mock.patch('tracpro.contacts.models.DataFieldManager.sync')
@override_settings(LANGUAGES=[
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
])
class TestOrgExtForm(TracProTest):
    form_class = forms.OrgExtForm

    def setUp(self):
        super(TestOrgExtForm, self).setUp()
        self.user = factories.User()
        self.data = {
            'name': 'Organization',
            'language': 'en',
            'available_languages': ['en', 'es'],
            'timezone': 'UTC',
            'created_by': self.user.pk,
            'modified_by': self.user.pk,
            'editors': [self.user.pk],
            'viewers': [self.user.pk],
            'administrators': [self.user.pk],
            'show_spoof_data': True,
            'subdomain': 'org',
            'how_to_handle_sameday_responses': SAMEDAY_LAST,
        }

    def test_subdomain_required(self, mock_sync):
        self.data.pop('subdomain')
        form = self.form_class(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['subdomain'])
        self.assertEqual(form.errors['subdomain'], ['This field is required.'])

    def test_available_languages_initial_for_create(self, mock_sync):
        """Available languages should default to empty list when creating an org."""
        form = self.form_class(instance=None)
        self.assertEqual(form.fields['available_languages'].initial, [])

    def test_available_languages_initial_for_update(self, mock_sync):
        """Available languages should be set from the instance to update."""
        org = factories.Org(available_languages=['en', 'es'])
        form = self.form_class(instance=org)
        self.assertEqual(form.fields['available_languages'].initial, ['en', 'es'])

    def test_default_language_required_for_create(self, mock_sync):
        """Form should require a default language for new orgs."""
        self.data.pop('language')
        form = self.form_class(data=self.data, instance=None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['language'])
        self.assertEqual(form.errors['language'], ['This field is required.'])

    def test_default_language_required_for_update(self, mock_sync):
        """Form should require a default language when updating an org."""
        self.data.pop('language')
        form = self.form_class(data=self.data, instance=factories.Org())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['language'])
        self.assertEqual(form.errors['language'], ['This field is required.'])

    def test_available_languages_required_for_create(self, mock_sync):
        """Form should require available languages for new orgs."""
        self.data.pop('available_languages')
        form = self.form_class(data=self.data, instance=None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['available_languages'])
        self.assertEqual(form.errors['available_languages'],
                         ['This field is required.'])

    def test_available_languages_required_for_update(self, mock_sync):
        """Form should require available languages for new orgs."""
        self.data.pop('available_languages')
        form = self.form_class(data=self.data, instance=factories.Org())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), ['available_languages'])
        self.assertEqual(form.errors['available_languages'],
                         ['This field is required.'])

    def test_default_language_not_in_available_languages(self, mock_sync):
        """Form should require that default language is in available languages."""
        self.data['language'] = 'fr'
        form = self.form_class(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.keys(), [NON_FIELD_ERRORS])
        self.assertEqual(form.errors[NON_FIELD_ERRORS],
                         ['Default language must be one of the languages '
                          'available for this organization.'])

    def test_available_languages_no_change(self, mock_sync):
        """Form should allow available languages to remain unchanged."""
        org = factories.Org(
            available_languages=['en', 'es'],
            language='en',
        )
        form = self.form_class(data=self.data, instance=org)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        org.refresh_from_db()
        self.assertEqual(org.available_languages, ['en', 'es'])
        self.assertEqual(org.language, 'en')

    def test_add_available_languages(self, mock_sync):
        """Form should allow addition of available language(s)."""
        org = factories.Org(
            available_languages=['en', 'es'],
            language='en',
        )
        self.data['available_languages'] = ['en', 'es', 'fr']
        form = self.form_class(data=self.data, instance=org)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        org.refresh_from_db()
        self.assertEqual(org.available_languages, ['en', 'es', 'fr'])
        self.assertEqual(org.language, 'en')

    def test_remove_available_languages(self, mock_sync):
        """Form should allow removal of available language(s)."""
        org = factories.Org(
            available_languages=['en', 'es'],
            language='en',
        )
        self.data['available_languages'] = ['en']
        form = self.form_class(data=self.data, instance=org)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        org.refresh_from_db()
        self.assertEqual(org.available_languages, ['en'])
        self.assertEqual(org.language, 'en')

    def test_remove_default_from_available(self, mock_sync):
        """Form should error if default language is removed from available languages."""
        org = factories.Org(
            available_languages=['en', 'es'],
            language='en',
        )
        self.data['available_languages'] = ['es']
        form = self.form_class(data=self.data, instance=org)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.keys(), [NON_FIELD_ERRORS])
        self.assertEqual(form.errors[NON_FIELD_ERRORS],
                         ['Default language must be one of the languages '
                          'available for this organization.'])

    def test_initial_google_analytics(self, mock_sync):
        # The form gets initialized with the org's current code
        org = factories.Org(google_analytics='UA-12345')
        form = self.form_class(instance=org)
        self.assertEqual(form.fields['google_analytics'].initial, 'UA-12345')

    def test_change_google_analytics(self, mock_sync):
        # You can change the GA code
        org = factories.Org(google_analytics='UA-12345')
        self.data['google_analytics'] = 'UA-54321'
        form = self.form_class(instance=org, data=self.data)
        self.assertTrue(form.is_valid())
        form.save()
        org.refresh_from_db()
        self.assertEqual('UA-54321', org.get_config('google_analytics'))

    def test_validate_google_analytics(self, mock_sync):
        # If entered, GA code must start with "UA"
        self.data['google_analytics'] = 'XA-54321'
        form = self.form_class(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('google_analytics', form.errors)

    def test_unset_google_analytics(self, mock_sync):
        # You can remove the tracking code by blanking the input field
        org = factories.Org(google_analytics='UA-12345')
        self.data['google_analytics'] = ''
        form = self.form_class(instance=org, data=self.data)
        self.assertTrue(form.is_valid())
        form.save()
        org.refresh_from_db()
        self.assertEqual('', org.get_config('google_analytics'))


class FetchRunsFormTest(TestCase):
    def test_no_input(self):
        # Should fail to validate
        form = FetchRunsForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('days', form.errors)

    def test_all_zeroes(self):
        # Should fail to validate
        form = FetchRunsForm(data={'days': '0'})
        self.assertFalse(form.is_valid())
        self.assertIn('days', form.errors)

    def test_non_numeric(self):
        # Should fail to validate
        form = FetchRunsForm(data={'days': 'zero'})
        self.assertFalse(form.is_valid())
        self.assertIn('days', form.errors)

    def test_non_integer(self):
        # should fail to validate
        form = FetchRunsForm(data={'days': '1.1'})
        self.assertFalse(form.is_valid())
        self.assertIn('days', form.errors)

    def test_some_numbers(self):
        # should validate, return integers
        form = FetchRunsForm(data={'days': '1'})
        self.assertTrue(form.is_valid())
        self.assertEqual({'days': 1}, form.cleaned_data)
