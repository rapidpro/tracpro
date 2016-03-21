from __future__ import unicode_literals

from .base import *  # noqa


CELERY_ALWAYS_EAGER = True

CELERY_ALWAYS_EAGER_PROPAGATES_EXCEPTIONS = True

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INTERNAL_IPS = ['127.0.0.1']

SECRET_KEY = 'secret-key' * 5

TEMPLATE_DEBUG = True

LOGGING['root']['handlers'] = ['console']

for logger in LOGGING.get('loggers', {}):
    LOGGING['loggers'][logger]['level'] = 'DEBUG'
