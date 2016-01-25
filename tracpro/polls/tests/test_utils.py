# coding=utf-8
from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from tracpro.test.cases import TracProTest

from .. import utils


class TestExtractWords(TracProTest):

    def test_extract_words(self):
        self.assertEqual(
            utils.extract_words("I think it's good", "eng"),
            ['think', 'good'])  # I and it's are stop words
        self.assertEqual(
            utils.extract_words("I think it's good", "kin"),
            ['think', "it's", 'good'])  # no stop words for kin
        self.assertEqual(
            utils.extract_words("قلم رصاص", "ara"),
            ['قلم', 'رصاص'])


class TestNaturalSortKey(TestCase):

    def test_category_sort(self):
        categories = ['11-20', '1-10', '<100', 'Other', '21-999', '21-99']
        categories.sort(key=utils.natural_sort_key)
        self.assertEqual(categories, ['1-10', '11-20', '21-99', '21-999', '<100', 'Other'])
