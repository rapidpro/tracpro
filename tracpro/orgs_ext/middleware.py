from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest

from temba_client.base import TembaAPIError


class HandleTembaAPIError(object):
    """ Catch all Temba exception errors """

    def process_exception(self, request, exception):
        if isinstance(exception, TembaAPIError):
            return HttpResponseBadRequest(
                _("Org does not have a valid API Key. " +
                  "Please edit the org through Site Manage or contact your administrator."))

        pass
