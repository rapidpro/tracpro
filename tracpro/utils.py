from django.conf import settings


def get_uuids(things):
    """
    Return an iterable of the 'uuid' attribute values of the things.

    The things can be anything with a 'uuid' attribute.
    """
    return [thing.uuid for thing in things]


def is_production():
    return hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT.endswith('production')


def dunder_to_chained_attrs(value, key):
    """
    If key is of the form "foo__bar__baz", then return value.foo.bar.baz
    """
    if '__' not in key:
        return getattr(value, key)
    first_key, rest_of_keys = key.split('__', 1)
    first_val = getattr(value, first_key)
    return dunder_to_chained_attrs(first_val, rest_of_keys)
