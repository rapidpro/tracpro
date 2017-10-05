from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.utils import six

from tracpro import get_version, __version__


class GetVersionTest(TestCase):
    def test_current_version(self):
        self.assertTrue(isinstance(__version__, six.text_type),
                        msg="version is not unicode: %r" % __version__)

    def test_valid_versions(self):
        self.assertEqual("1.2.3", get_version((1, 2, 3, 'final')))
        self.assertEqual("1.2.3.dev", get_version((1, 2, 3, 'dev')))

    def test_three_part(self):
        with self.assertRaises(AssertionError):
            get_version((1, 2, 3))

    def test_non_integer(self):
        with self.assertRaises(AssertionError):
            get_version(("1", 2, 3, 'dev'))
