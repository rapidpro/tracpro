import json

from django.test import TestCase

from dash.orgs import models

from ..utils import OrgConfigField


class TestOrgConfigField(TestCase):

    def setUp(self):
        """Create a temporary OrgConfigField for test purposes."""
        super(TestOrgConfigField, self).setUp()
        models.Org.test_field = OrgConfigField("test_field")

    def tearDown(self):
        """Remove the temporary test OrgConfigField."""
        super(TestOrgConfigField, self).tearDown()
        del(models.Org.test_field)

    def test_get__config_is_none(self):
        """OrgConfigField can be retrieved when config is not set."""
        org = models.Org(config=None)
        self.assertEqual(org.test_field, None)

    def test_get__field_not_in_config(self):
        """OrgConfigField can be retrieved if field is not in config dict."""
        org = models.Org(config=json.dumps({'another': "hello"}))
        self.assertEqual(org.test_field, None)

    def test_get__field_in_config(self):
        """OrgConfigField can be retrieved from config dict."""
        org = models.Org(config=json.dumps({'test_field': "hello"}))
        self.assertEqual(org.test_field, "hello")

    def test_set__config_is_none(self):
        """OrgConfigField can be set when config is not originally set."""
        org = models.Org(config=None)
        org.test_field = "hello"
        self.assertEqual(org.test_field, "hello")
        self.assertEqual(org.config, json.dumps({'test_field': "hello"}))

    def test_set__field_not_in_config(self):
        """OrgConfigField can add a new field to the config dict."""
        org = models.Org(config=json.dumps({'another': "hello"}))
        org.test_field = "hello"
        self.assertEqual(org.test_field, "hello")
        self.assertEqual(org.config, json.dumps({
            'test_field': "hello",
            'another': "hello",
        }))

    def test_set__override_existing(self):
        """OrgConfigField can override an existing value in the config dict."""
        org = models.Org(config=json.dumps({'test_field': "old_value"}))
        org.test_field = "hello"
        self.assertEqual(org.test_field, "hello")
        self.assertEqual(org.config, json.dumps({'test_field': "hello"}))

    def test_workflow__manually_set_config(self):
        """Cache workflow when config dict is manually set."""
        org = models.Org(config=None)
        self.assertEqual(org.test_field, None)  # sets _test_field
        org.config = json.dumps({'test_field': "hello"})
        self.assertEqual(org.test_field, None)  # uses existing _test_field
        del org._test_field
        self.assertEqual(org.test_field, "hello")

    def test_workflow__manually_override_cache_field(self):
        """Cache workflow when cache field is manually set."""
        org = models.Org(config=None)
        self.assertEqual(org.test_field, None)
        org._test_field = "hello"
        self.assertEqual(org.config, None)
        self.assertEqual(org.test_field, "hello")

    def test_workflow__set_busts_cache(self):
        """Cache workflow when config field is set through OrgConfigField."""
        org = models.Org(config=None)
        self.assertFalse(hasattr(org, "_test_field"))  # cached value not set
        self.assertEqual(org.test_field, None)  # sets _test_field
        self.assertEqual(org._test_field, None)
        org.test_field = "hello"  # deletes _test_field
        self.assertFalse(hasattr(org, "_test_field"))
        self.assertEqual(org.test_field, "hello")  # sets _test_field
        self.assertEqual(org._test_field, "hello")
