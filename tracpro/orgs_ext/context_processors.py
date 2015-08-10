from django.conf import settings


def user_is_admin(request):
    org = request.org
    is_admin = org and request.user.is_authenticated() and request.user.is_admin_for(org)
    return {
        'user_is_admin': is_admin,
    }


def available_languages(request):
    languages = settings.LANGUAGES
    org = getattr(request, 'org')
    if org:
        if org.available_languages:
            languages = filter(lambda lang: lang[0] in org.available_languages, languages)
    return {
        'available_languages': languages,
    }
