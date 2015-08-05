from __future__ import unicode_literals

from .base import *  # noqa


CELERY_ALWAYS_EAGER = True

CELERY_ALWAYS_EAGER_PROPAGATES_EXCEPTIONS = True

DEBUG = True

INTERNAL_IPS = ['127.0.0.1']

SECRET_KEY = 'secret-key' * 5

TEMPLATE_DEBUG = True

for logger in LOGGING.get('loggers', {}):
    LOGGING['loggers'][logger]['handlers'] = ['console']
