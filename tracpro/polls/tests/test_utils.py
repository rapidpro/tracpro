# coding=utf-8
from __future__ import absolute_import, unicode_literals

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
