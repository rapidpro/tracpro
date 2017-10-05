from __future__ import unicode_literals

import logging

from .base import *  # noqa


# Don't display logging during tests.
logging.disable(logging.CRITICAL)

BROKER_URL = CELERY_RESULT_BACKEND = 'redis://localhost:6379/10'

CELERY_ALWAYS_EAGER = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

SECRET_KEY = 'secret-key' * 5

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
