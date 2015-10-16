from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest

from temba_client.base import TembaAPIError, TembaConnectionError


class HandleTembaAPIError(object):
    """ Catch all Temba exception errors """

    def process_exception(self, request, exception):

        rapidProConnectionErrorString = _(
            "RapidPro appears to be down right now. "
            "Please try again later.")

        if isinstance(exception, TembaAPIError):
            rapidpro_connection_error_codes = ["502", "503", "504"]

            if any(code in exception.caused_by.message for code in rapidpro_connection_error_codes):
                return HttpResponseBadRequest(
                    rapidProConnectionErrorString)

            else:
                return HttpResponseBadRequest(
                    _("Org does not have a valid API Key. "
                      "Please edit the org through Site Manage or contact your administrator."))

        elif isinstance(exception, TembaConnectionError):
            return HttpResponseBadRequest(
                rapidProConnectionErrorString)

        pass
