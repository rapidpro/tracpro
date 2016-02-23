from decimal import Decimal, InvalidOperation
from functools import wraps

from django.utils.translation import ugettext


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
    """Return the names of all answer categories, and Other."""
    categories = [get_category(rule) for rule in question.get_rules()]
    # Use non-lazy evaluation to ensure the list is JSON-serializable.
    categories.append(ugettext("Other"))
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
