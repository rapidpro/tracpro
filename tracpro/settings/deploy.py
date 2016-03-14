from __future__ import unicode_literals

from .base import *  # noqa


require_env('DB_NAME', 'DB_USER', 'DOMAIN', 'ENVIRONMENT', 'SECRET_KEY')

DOMAIN = from_env('DOMAIN')

ENVIRONMENT = from_env('ENVIRONMENT').lower()

WEBSERVER_ROOT = '/var/www/tracpro/'

ADMINS = [
    ('Caktus EduTrac Team', 'edutrac-team@caktusgroup.com'),
]

ALLOWED_HOSTS = [".{}".format(DOMAIN)]

CACHES['default']['LOCATION'] = 'localhost:6379:4'

CELERY_SEND_TASK_ERROR_EMAILS = True

COMPRESS_CSS_HASHING_METHOD = 'content'

COMPRESS_OFFLINE = True

COMPRESS_OFFLINE_CONTEXT = {
    'STATIC_URL': STATIC_URL,
    'base_template': 'frame.html',
    'debug': False,
    'testing': False,
}

CSRF_COOKIE_DOMAIN = ".{}".format(DOMAIN)

DATABASES['default'].update({
    'NAME': from_env('DB_NAME', ''),
    'USER': from_env('DB_USER', ''),
    'HOST': from_env('DB_HOST', ''),
    'PORT': from_env('DB_PORT', ''),
    'PASSWORD': from_env('DB_PASSWORD', ''),
})

DEFAULT_FROM_EMAIL = "no-reply@{}".format(DOMAIN)

EMAIL_HOST = from_env_or_django('EMAIL_HOST')

EMAIL_HOST_PASSWORD = from_env_or_django('EMAIL_HOST_PASSWORD')

EMAIL_HOST_USER = from_env_or_django('EMAIL_HOST_USER')

EMAIL_SUBJECT_PREFIX = '[Edutrac {}]'.format(ENVIRONMENT.title())

EMAIL_USE_SSL = from_env_or_django('EMAIL_USE_SSL')

EMAIL_USE_TLS = from_env_or_django('EMAIL_USE_TLS')

EMAIL_PORT = from_env('EMAIL_PORT', 587 if EMAIL_USE_TLS else 465 if EMAIL_USE_SSL else 25)

HOSTNAME = DOMAIN

MEDIA_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'media')

SECRET_KEY = from_env('SECRET_KEY')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'HTTPS')

SERVER_EMAIL = "no-reply@{}".format(DOMAIN)

SESSION_CACHE_ALIAS = "default"

SESSION_COOKIE_DOMAIN = ".{}".format(DOMAIN)

SESSION_COOKIE_SECURE = False

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

STATIC_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'static')
