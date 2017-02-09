from django.conf import settings
from temba_client.clients import CursorQuery
from temba_client.v2 import TembaClient


def get_client(org):
    host = getattr(settings, 'SITE_API_HOST', None)
    agent = getattr(settings, 'SITE_API_USER_AGENT', None)
    return make_client(host, org.api_token, user_agent=agent)


def make_client(host, api_token, user_agent):
    # This method looks pointless, but it lets us mock it easily
    # and change every call that returns a client.
    return TracProClient(host, api_token, user_agent=user_agent)


class TracProClient(TembaClient):
    """
    Customized TembaClient where the API calls that return multiple things
    actually return them without having to tack on .all().

    (Does this by returning a TracProCursorQuery instead of a CursorQuery.
    Apart from being iterable-over, it should work the same.)
    """
    def _get_query(self, endpoint, params, clazz):
        """
        GETs a result query for the given endpoint
        """
        return TracProCursorQuery(self, '%s/%s.json' % (self.root_url, endpoint), params, clazz)


class TracProCursorQuery(CursorQuery):
    """
    Customized CursorQuery that allows iterating over it without having
    to call `.all()` on it. More Pythonic.
    """
    def __iter__(self):
        # Call the superclass's .all() because we've overridden the one on this
        # class to still act the same as the one on the parent class.
        return super(TracProCursorQuery, self).all(True).__iter__()

    def all(self, retry_on_rate_exceed=False):
        # If code calls .all() on this, behave like the old one
        return self.__iter__()
