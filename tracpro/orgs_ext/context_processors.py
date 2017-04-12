from __future__ import unicode_literals

from django.conf import settings


def user_is_admin(request):
    org = request.org
    is_admin = org and request.user.is_authenticated() and request.user.is_admin_for(org)
    return {
        'user_is_admin': is_admin,
    }


def available_languages(request):
    all_languages = settings.LANGUAGES
    org = getattr(request, 'org')
    if org and org.available_languages:
        show_languages = [code for code, name in all_languages
                          if code in org.available_languages or code == request.LANGUAGE_CODE]
    else:
        show_languages = [code for code, name in all_languages]
    return {
        'all_languages': all_languages,
        'show_languages': show_languages
    }


def google_analytics(request):
    """
    If the org has a Google Analytics tracking code, include
    it in the context as 'google_analytics'
    """
    if request.org:
        ga = request.org.get_config('google_analytics', False)
        if ga:
            return {
                'google_analytics': ga
            }
    return {}
