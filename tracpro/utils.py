def get_uuids(things):
    """
    Return an iterable of the 'uuid' attribute values of the things.

    The things can be anything with a 'uuid' attribute.
    """
    return [thing.uuid for thing in things]
