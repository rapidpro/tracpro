from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from requests import RequestException

from dash.orgs import middleware as dash_middleware
from temba_client.exceptions import TembaConnectionError, TembaTokenError


class TracproOrgMiddleware(dash_middleware.SetOrgMiddleware):

    def user_has_set_language(self, request):
        """Whether user has requested a specific language via site footer."""
        return any((
            request.session.get(translation.LANGUAGE_SESSION_KEY),
            request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME),
        ))

    def set_language(self, request, org):
        """
        Use the org's default language unless user has selected a specific
        language.
        """
        if org and org.language and not self.user_has_set_language(request):
            lang = org.language
            translation.activate(lang)
            request.LANGUAGE_CODE = lang


class HandleTembaAPIError(object):
    """ Catch all Temba exception errors """

    def process_exception(self, request, exception):
        rapidpro_connection_error_string = _(
            "RapidPro appears to be down right now. "
            "Please try again later.")

        if isinstance(exception, TembaTokenError):
            return self.rapidpro_error(
                request,
                _("Org does not have a valid API Key. "
                  "Please edit the org through Site Manage or contact your administrator.")
                )

        elif isinstance(exception, TembaConnectionError):
            return self.rapidpro_error(request, rapidpro_connection_error_string)

        elif isinstance(exception, RequestException):
            response = exception.response
            if response.status_code >= 500:
                return self.rapidpro_error(request, rapidpro_connection_error_string)

        return None

    def rapidpro_error(self, request, message):
        return render(request, "rapidpro_error.html", {"error_message": message}, status=400)
