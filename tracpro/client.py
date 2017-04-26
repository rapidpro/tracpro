import logging
from django.conf import settings
from temba_client.clients import CursorQuery
from temba_client.v2 import Boundary, TembaClient


logger = logging.getLogger(__name__)


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

    def get_boundaries(self):
        return self._get_query('boundaries', {'geometry': 'true'}, Boundary)

    def get_contacts_in_groups(self, group_uuids, deleted=None):
        """
        Get all contacts from RapidPro that are in a list of groups,
        only including each contact once.

        :param group_uuids: array of uuids and/or names
        :param deleted: return deleted contacts only
        :return: iterable of TembaContact objects

        https://app.rapidpro.io/api/v2/contacts
        """
        logger.info("get_contacts_in_groups(%d groups, deleted=%s)..." % (len(group_uuids), deleted))
        contact_by_uuid = {}
        for uuid in group_uuids:
            from groups.models import Group
            grp = Group.objects.get(uuid=uuid)
            logger.info("start fetch for group %s..." % grp.name)
            contact_by_uuid.update(
                {contact.uuid: contact
                 for contact in self.get_contacts(deleted=deleted, group=uuid)})
            logger.info("finished fetch for group %s" % uuid)
        return contact_by_uuid.values()


class TracProCursorQuery(CursorQuery):
    """
    Customized CursorQuery that allows iterating over it without having
    to call `.all()` on it. More Pythonic.

    FYI: Always acts as if `retry_on_rate_exceed` is True. If more control
    is needed, use the underlying client directly.
    """
    def _get_result(self):
        if not hasattr(self, '_result'):
            self._result = self.all(True)
        return self._result

    def __iter__(self):
        return self._get_result().__iter__()

    def __getitem__(self, index):
        return self._get_result()[index]
