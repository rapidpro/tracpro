import json

from django.test import TestCase

from dash.orgs import models

from . import factories


class TestOrgExt(TestCase):

    def test_get_available_languages_default(self):
        """available_languages should return an empty list if it is not set."""
        org = models.Org()
        self.assertEqual(org.available_languages, [])

    def test_get_available_languages(self):
        """available_languages should be read from the config field."""
        org = models.Org()
        org.config = json.dumps({'available_languages': ['en', 'es']})
        self.assertEqual(org.available_languages, ['en', 'es'])

    def test_set_available_languages(self):
        """Setting available_languages should update the config field."""
        org = models.Org()
        org.available_languages = ['en', 'es']
        self.assertEqual(org.config, json.dumps({'available_languages': ['en', 'es']}))
        self.assertEqual(org.available_languages, ['en', 'es'])
