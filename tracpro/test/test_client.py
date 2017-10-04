"""
Tests for our client wrapper
"""
from django.test import TestCase

from tracpro.client import TracProCursorQuery


class TracproClientTest(TestCase):
    def test_access_as_boolean_when_empty(self):
        # Our query cursor works right when we just say "if cursor:"
        cursor = TracProCursorQuery(None, None, None, None)
        cursor._result = []
        self.assertFalse(cursor)

    def test_access_as_boolean_when_not_empty(self):
        # Our query cursor works right when we just say "if cursor:"
        cursor = TracProCursorQuery(None, None, None, None)
        cursor._result = [1]
        self.assertTrue(cursor)
