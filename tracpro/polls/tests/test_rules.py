from __future__ import unicode_literals

from tracpro.test.cases import TracProTest

from .. import rules
from . import factories


class TestGetCategory(TracProTest):

    def _create_rule(self, category):
        return {
            'category': category,
            'test': {},
        }

    def test_get_category_direct(self):
        """Return rule['category'] if it is not a dictionary."""
        rule = self._create_rule('cats')
        self.assertEqual(rules.get_category(rule), "cats")

    def test_get_category_base(self):
        """get_category returns the base category name, if available."""
        rule = self._create_rule({'base': 'base', 'eng': 'eng'})
        self.assertEqual(rules.get_category(rule), "base")

    def test_get_category_other(self):
        """get_category returns the first available translation."""
        rule = self._create_rule({'eng': 'eng'})
        self.assertEqual(rules.get_category(rule), "eng")


class TestGetAllCategories(TracProTest):

    def _create_rule(self, category):
        return {
            'category': {'base': category},
            'test': {},
        }

    def test_get_all_no_rules(self):
        question = factories.Question(rules=[])
        self.assertEqual(rules.get_all_categories(question), ["Other"])

    def test_get_all(self):
        question = factories.Question(rules=[
            self._create_rule('a'),
            self._create_rule('b'),
        ])
        self.assertEqual(
            rules.get_all_categories(question),
            ['a', 'b', 'Other'])

    def test_get_all__include_other(self):
        """Ensure that "Other" is at the end of the list."""
        question = factories.Question(rules=[
            self._create_rule('a'),
            self._create_rule('Other'),
            self._create_rule('b'),
        ])
        self.assertEqual(
            rules.get_all_categories(question),
            ['a', 'b', 'Other'])

    def test_get_all_with_answers(self):
        """Include Answer categories that aren't in the rules."""
        question = factories.Question(rules=[
            self._create_rule('a'),
            self._create_rule('b'),
        ])
        factories.Answer(question=question, category='apple')
        factories.Answer(question=question, category='a')
        self.assertEqual(
            rules.get_all_categories(question, answers=question.answers.all()),
            ['a', 'b', 'apple', 'Other'])

    def test_duplicates(self):
        question = factories.Question(rules=[
            self._create_rule('b'),
            self._create_rule('a'),
            self._create_rule('a'),
            self._create_rule('b'),
        ])
        self.assertEqual(
            rules.get_all_categories(question),
            ['b', 'a', 'Other'])


class CheckRuleTestBase(object):

    def call(self, test):
        val, kwargs = test
        return self.rule(val, **kwargs)

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


class TestIsNumber(CheckRuleTestBase, TracProTest):
    rule = staticmethod(rules.is_number)
    true_tests = [
        ("1.234", {}),
        ("1", {}),
        ("0", {}),
        ("-1", {}),
        ("-1.23", {}),
    ]
    false_tests = [
        (None, {}),
        ("asdf", {}),
        ("1.asdf", {}),
        ("asdf.1", {}),
        ("asdf1", {}),
        ("1asdf", {}),
    ]


class TestIsBetween(CheckRuleTestBase, TracProTest):
    rule = staticmethod(rules.is_between)
    true_tests = [
        ("1", {'min': "1", 'max': "2"}),
        ("1.5", {'min': "1", 'max': "2"}),
        ("2", {'min': "1", 'max': "2"}),
    ]
    false_tests = [
        (None, {'min': "1", 'max': "2"}),
        ("asdf", {'min': "1", 'max': "2"}),
        ("1", {'min': None, 'max': "2"}),
        ("1", {'min': "1", 'max': None}),
        ("1", {'min': "asdf", 'max': "2"}),
        ("1", {'min': "1", 'max': "asdf"}),
        ("0.9", {'min': "1", 'max': "2"}),
        ("1.5", {'min': "2", 'max': "1"}),
    ]


class TestIsEqual(CheckRuleTestBase, TracProTest):
    rule = staticmethod(rules.is_equal)
    true_tests = [
        ("1.0", {'test': "1"}),
        ("1", {'test': "1.0"}),
    ]
    false_tests = [
        ("1", {'test': "1.01"}),
        ("asdf", {'test': "1"}),
        ("1", {'test': "asdf"}),
        (None, {'test': "1"}),
    ]


class TestIsLessThan(CheckRuleTestBase, TracProTest):
    rule = staticmethod(rules.is_less_than)
    true_tests = [
        ("1", {'test': "1.5"}),
        ("1.5", {'test': "2"}),
        ("-1", {'test': "1"}),
    ]
    false_tests = [
        ("1.5", {'test': "1"}),
        ("1.0", {'test': "1"}),
        (None, {'test': "1"}),
        ("asdf", {'test': "1"}),
        ("1", {'test': "asdf"}),
    ]


class TestIsGreaterThan(CheckRuleTestBase, TracProTest):
    rule = staticmethod(rules.is_greater_than)
    true_tests = [
        ("1.5", {'test': "1"}),
        ("2", {'test': "1.5"}),
        ("1", {'test': "-1"}),
    ]
    false_tests = [
        ("1", {'test': "1.5"}),
        ("1.0", {'test': "1"}),
        (None, {'test': "-1"}),
        ("asdf", {'test': "1"}),
        ("1", {'test': "asdf"}),
    ]
