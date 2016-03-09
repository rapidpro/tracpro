from __future__ import unicode_literals

from .base import *  # noqa


require_env('DOMAIN', 'ENVIRONMENT')

ENVIRONMENT = from_env('ENVIRONMENT').lower()

WEBSERVER_ROOT = '/var/www/tracpro/'

ADMINS = [
    ('Caktus EduTrac Team', 'edutrac-team@caktusgroup.com'),
]

ALLOWED_HOSTS = ['.' + from_env('DOMAIN')]

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

CSRF_COOKIE_DOMAIN = from_env_or_django('CSRF_COOKIE_DOMAIN')

DATABASES['default'].update({
    'NAME': 'tracpro_{}'.format(ENVIRONMENT),
    'USER': 'tracpro_{}'.format(ENVIRONMENT),
    'HOST': from_env('DB_HOST', ''),
    'PORT': from_env('DB_PORT', ''),
    'PASSWORD': from_env('DB_PASSWORD', ''),
})

DEFAULT_FROM_EMAIL = 'no-reply@caktusgroup.com'

EMAIL_SUBJECT_PREFIX = '[Edutrac {}]'.format(ENVIRONMENT.title())

HOSTNAME = from_env('DOMAIN')

LOGGING['handlers']['file']['filename'] = os.path.join(WEBSERVER_ROOT, 'log', 'tracpro.log')

MEDIA_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'media')

SECRET_KEY = from_env('SECRET_KEY')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'HTTPS')

SESSION_CACHE_ALIAS = "default"

SESSION_COOKIE_DOMAIN = from_env('SESSION_COOKIE_DOMAIN')

SESSION_COOKIE_SECURE = False

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SITE_HOST_PATTERN = from_env('SITE_HOST_PATTERN')

STATIC_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'static')
