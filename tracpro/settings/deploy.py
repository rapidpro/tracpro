from __future__ import unicode_literals

from .base import *  # noqa


WEBSERVER_ROOT = '/var/www/tracpro/'

ENVIRONMENT = os.environ.get('ENVIRONMENT', '').lower()

ADMINS = [
    ('Caktus Website Team', 'website-team@caktusgroup.com'),
]

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(';')

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

DATABASES['default'].update({
    'NAME': 'tracpro_{}'.format(ENVIRONMENT),
    'USER': 'tracpro_{}'.format(ENVIRONMENT),
    'HOST': os.environ.get('DB_HOST', ''),
    'PORT': os.environ.get('DB_PORT', ''),
    'PASSWORD': os.environ.get('DB_PASSWORD', ''),
})

DEFAULT_FROM_EMAIL = 'no-reply@caktusgroup.com'

EMAIL_SUBJECT_PREFIX = '[Edutrac] '

HOSTNAME = 'tracpro.staging.nyaruka.com'

LOGGING['handlers']['file']['filename'] = os.path.join(WEBSERVER_ROOT, 'log', 'tracpro.log')

MEDIA_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'media')

SECRET_KEY = os.environ.get('SECRET_KEY', '')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'HTTPS')

SESSION_CACHE_ALIAS = "default"

SESSION_COOKIE_DOMAIN = 'tracpro.staging.nyaruka.com'

SESSION_COOKIE_SECURE = False

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SITE_API_HOST = 'http://textit.staging.nyaruka.com/api/v1'

SITE_HOST_PATTERN = 'http://%s.tracpro.staging.nyaruka.com'

STATIC_ROOT = os.path.join(WEBSERVER_ROOT, 'public', 'static')
