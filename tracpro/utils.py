from django.conf import settings


def get_uuids(things):
    """
    Return an iterable of the 'uuid' attribute values of the things.

    The things can be anything with a 'uuid' attribute.
    """
    return [thing.uuid for thing in things]


def is_production():
    return hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT.endswith('production')
