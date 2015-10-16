from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseBadRequest

from requests import HTTPError

from temba_client.base import TembaAPIError, TembaConnectionError


class HandleTembaAPIError(object):
    """ Catch all Temba exception errors """

    def process_exception(self, request, exception):

        rapidProConnectionErrorString = _(
            "RapidPro appears to be down right now. "
            "Please try again later.")

        if isinstance(exception, TembaAPIError):
            if isinstance(exception.caused_by, HTTPError):
                response = exception.caused_by.response
                if response is not None:
                    if response.status_code == 403:
                        return HttpResponseBadRequest(
                            _("Org does not have a valid API Key. "
                              "Please edit the org through Site Manage or contact your administrator."))

                    elif response.status_code >= 500:
                        return HttpResponseBadRequest(rapidProConnectionErrorString)

        elif isinstance(exception, TembaConnectionError):
            return HttpResponseBadRequest(
                rapidProConnectionErrorString)

        return None
