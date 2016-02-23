from django.test import TestCase

from .. import rules
from . import factories


class TestGetCategory(TestCase):

    def create_rule(self, category):
        return {
            'category': category,
            'test': {},
        }

    def test_get_category_direct(self):
        """Return rule['category'] if it is not a dictionary."""
        rule = self.create_rule('cats')
        self.assertEqual(rules.get_category(rule), "cats")

    def test_get_category_base(self):
        """get_category returns the base category name, if available."""
        rule = self.create_rule({'base': 'base', 'eng': 'eng'})
        self.assertEqual(rules.get_category(rule), "base")

    def test_get_category_other(self):
        """get_category returns the first available translation."""
        rule = self.create_rule({'eng': 'eng'})
        self.assertEqual(rules.get_category(rule), "eng")


class TestGetAllCategories(TestCase):

    def create_rule(self, category):
        return {
            'category': {'base': category},
            'test': {},
        }

    def test_get_all_no_rules(self):
        question = factories.Question(rules=[])
        self.assertEqual(rules.get_all_categories(question), ["Other"])

    def test_get_all(self):
        question = factories.Question(rules=[
            self.create_rule('example'),
            self.create_rule('test'),
        ])
        self.assertEqual(
            rules.get_all_categories(question),
            ['example', 'test', 'Other'])


class CheckRuleTestBase(object):

    def test_false(self):
        unexpected_successes = []
        for test in self.false_tests:
            if self.call(test) is not False:
                unexpected_successes.append(test)
        if unexpected_successes:
            self.fail(
                "Test did not fail for these inputs:\n" +
                "\n".join(str(s) for s in unexpected_successes))

    def test_true(self):
        unexpected_failures = []
        for test in self.true_tests:
            if self.call(test) is not True:
                unexpected_failures.append(test)
        if unexpected_failures:
            self.fail(
                "Test did not succeed for these inputs:\n" +
                "\n".join(str(f) for f in unexpected_failures))


class TestIsNumeric(CheckRuleTestBase, TestCase):
    true_tests = ["1.234", "1", "0", "-1", "-1.23"]
    false_tests = [None, "asdf", "1.asdf", "asdf.1", "asdf1", "1asdf"]

    def call(self, test):
        return rules.is_numeric(test)


class TestIsBetween(CheckRuleTestBase, TestCase):
    true_tests = [
        ("1", "1", "2"),
        ("1.5", "1", "2"),
        ("2", "1", "2"),
    ]
    false_tests = [
        (None, "1", "2"),
        ("asdf", "1", "2"),
        ("1", None, "2"),
        ("1", "1", None),
        ("1", "asdf", "2"),
        ("1", "1", "asdf"),
        ("0.9", "1", "2"),
        ("1.5", "2", "1"),
    ]

    def call(self, test):
        return rules.is_between(*test)


class TestIsEqual(CheckRuleTestBase, TestCase):
    true_tests = [
        ("1.0", "1"),
        ("1", "1.0"),
    ]
    false_tests = [
        ("1", "1.01"),
        ("asdf", "1"),
        ("1", "asdf"),
        (None, "1"),
    ]

    def call(self, test):
        return rules.is_equal(*test)


class TestIsLessThan(CheckRuleTestBase, TestCase):
    true_tests = [
        ("1", "1.5"),
        ("1.5", "2"),
        ("-1", "1"),
    ]
    false_tests = [
        ("1.5", "1"),
        ("1.0", "1"),
        (None, "1"),
        ("asdf", "1"),
        ("1", "asdf"),
    ]

    def call(self, test):
        return rules.is_less_than(*test)


class TestIsGreaterThan(CheckRuleTestBase, TestCase):
    true_tests = [
        ("1.5", "1"),
        ("2", "1.5"),
        ("1", "-1"),
    ]
    false_tests = [
        ("1", "1.5"),
        ("1.0", "1"),
        (None, "-1"),
        ("asdf", "1"),
        ("1", "asdf"),
    ]

    def call(self, test):
        return rules.is_greater_than(*test)
