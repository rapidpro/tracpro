from decimal import Decimal, InvalidOperation
from functools import wraps

from django.utils.translation import ugettext_lazy as _


# Rule tests that suggest that the expected data is numeric.
NUMERIC_TESTS = ('number', 'lt', 'eq', 'gt', 'between')


def get_category(rule):
    """Return the rule category name."""
    if isinstance(rule['category'], dict):
        if 'base' in rule['category']:
            return rule['category']['base']
        # Keys are the languages that the category name is translated in.
        # Return the first translation.
        return rule['category'].values()[0]
    return rule['category']


def get_all_categories(question):
    """Return the names of all possible Answer categories, and Other."""
    categories = []

    # Add categories in the order they are defined on RapidPro.
    for rule in question.get_rules():
        category = get_category(rule)
        if category not in categories:
            categories.append(category)

    # Flow definitions change over time.
    # Find any categories that aren't in the rules.
    extra = question.answers.exclude(category__in=categories + [''])
    extra = extra.exclude(category=None)
    extra = extra.values_list('category', flat=True).distinct('category')
    for category in extra:
        if category not in categories:
            categories.append(category)

    # The last category should be "Other."
    other = str(_("Other"))  # Evaluate to keep the list JSON serializable.
    if other in categories:
        categories.remove(other)
    categories.append(other)

    return categories


def passes_test(value, rule):
    """Returns whether the value passes the rule test.

    `rule_test` is in the format returned by RapidPro, for example:

        {'type': 'between', 'min': 5, 'max': 10}

    Currently only numeric types are implemented.
    All other test types will return False.
    """
    test = rule['test'].copy()
    test_funcs = {
        'numeric': is_numeric,
        'between': is_between,
        'eq': is_equal,
        'lt': is_less_than,
        'gt': is_greater_than,
    }

    test_func = test_funcs.get(test.pop('type'))
    return test_func(value, **test) if test_func else False


def numeric_rule(function):
    """Rule test decorator that returns False if any argument is non-numeric."""
    @wraps(function)
    def wrapped(value, *args, **kwargs):
        try:
            numeric = Decimal(value)
            args = [Decimal(a) for a in args]
            kwargs = {k: Decimal(v) for k, v in kwargs.items()}
        except (TypeError, InvalidOperation):
            return False
        return function(numeric, *args, **kwargs)
    return wrapped


@numeric_rule
def is_numeric(val):
    return True  # Decorator ensures that the argument is numeric.


@numeric_rule
def is_between(val, min, max):
    return min <= val <= max


@numeric_rule
def is_equal(val, test):
    return val == test


@numeric_rule
def is_less_than(val, test):
    return val < test


@numeric_rule
def is_greater_than(val, test):
    return val > test
