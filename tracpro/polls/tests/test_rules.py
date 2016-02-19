from django.test import TestCase

from .. import rules


class RuleTestBase(object):
    true_tests = []  # Input that the rule test should return True for.
    false_tests = []  # Input that the rule test should return False for.

    def call(self, test):
        self.fail("Subclass should implement this.")

    def test_false(self):
        unexpected_successes = []
        for test in self.false_tests:
            if self.call(test):
                unexpected_successes.append(test)
        if unexpected_successes:
            self.fail(
                "Test passed unexpectedly for these inputs:\n" +
                "\n".join(str(s) for s in unexpected_successes))

    def test_true(self):
        unexpected_failures = []
        for test in self.true_tests:
            if not self.call(test):
                unexpected_failures.append(test)
        if unexpected_failures:
            self.fail(
                "Test failed unexpectedly for these inputs:\n" +
                "\n".join(str(f) for f in unexpected_failures))


class TestIsNumeric(RuleTestBase, TestCase):
    true_tests = ["1.234", "1", "0", "-1", "-1.23"]
    false_tests = [None, "asdf", "1.asdf", "asdf.1", "asdf1", "1asdf"]

    def call(self, test):
        return rules.is_numeric(test)


class TestIsBetween(RuleTestBase, TestCase):
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


class TestIsEqual(RuleTestBase, TestCase):
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


class TestIsLessThan(RuleTestBase, TestCase):
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


class TestIsGreaterThan(RuleTestBase, TestCase):
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
