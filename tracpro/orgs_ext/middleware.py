from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render

from requests import HTTPError

from temba_client.base import TembaAPIError, TembaConnectionError


class HandleTembaAPIError(object):
    """ Catch all Temba exception errors """

    def process_exception(self, request, exception):

        rapidpro_connection_error_string = _(
            "RapidPro appears to be down right now. "
            "Please try again later.")

        if isinstance(exception, TembaAPIError):
            if isinstance(exception.caused_by, HTTPError):
                response = exception.caused_by.response
                if response is not None:
                    if response.status_code == 403:
                        return self.rapidpro_error(
                            request,
                            _("Org does not have a valid API Key. "
                              "Please edit the org through Site Manage or contact your administrator.")
                            )

                    elif response.status_code >= 500:
                        return self.rapidpro_error(request, rapidpro_connection_error_string)

        elif isinstance(exception, TembaConnectionError):
            return self.rapidpro_error(request, rapidpro_connection_error_string)

        return None

    def rapidpro_error(self, request, message):
        return render(request, "rapidpro_error.html", {"error_message": message}, status=400)
