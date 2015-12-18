import logging

from requests import HTTPError

from temba_client.base import TembaAPIError


logger = logging.getLogger(__name__)


class OrgConfigField(object):
    """
    Allows setting and retrieving of a config field as if it were a normal
    class attribute.

    The result of the initial retrieval is cached on the object.
    This avoids reloading the JSON-encoded config each time that the field is
    accessed. The retrieval cache is busted when the value is set.

    Usage::

        >>> Org.add_to_class('config_field', OrgConfigField('config_field'))
        >>> print(Org.config_field)  # calls get_config and caches result
        None
        >>> Org.config_field = "hello"  # calls set_config and busts cache
        >>> print(Org.config_field)  # calls get_config and caches result
        hello
        >>> print(Org.config_field)  # uses cached result
        hello

    """

    def __init__(self, name):
        # The key used to store this field in the instance's config.
        self.name = name
        # Where the cached value of the field is stored on the instance.
        self.cache_name = "_{}".format(name)

    def __get__(self, instance, owner):
        if not instance:
            return self
        if self.cache_name not in instance.__dict__:
            val = instance.get_config(self.name)
            instance.__dict__[self.cache_name] = val
        return instance.__dict__[self.cache_name]

    def __set__(self, instance, value):
        instance.set_config(self.name, value, commit=False)
        instance.__dict__.pop(self.cache_name, None)


def run_org_task(org, task):
    """Common protocol for running a task for an Org."""
    task_name = task.__name__

    if not org.api_token:
        msg = "{}: Skipping {} because it does not have an API token."
        logger.info(msg.format(task_name, org))
        return None

    try:
        return task(org.pk)
    except TembaAPIError as e:
        if caused_by_bad_api_key(e):
            msg = "{}: API token for {} is invalid."
            logger.warning(msg.format(task_name, org), exc_info=True)
            return None
        raise


def caused_by_bad_api_key(exception):
    """Return whether the exception was likely caused by a bad API key."""
    if isinstance(exception, TembaAPIError):
        if isinstance(exception.caused_by, HTTPError):
            response = exception.caused_by.response
            if response is not None and response.status_code == 403:
                return True
    return False
