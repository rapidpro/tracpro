from __future__ import unicode_literals

import datetime
import os

import djcelery

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _


djcelery.setup_loader()

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
))

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:10',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tracpro',
        'CONN_MAX_AGE': 60,
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {},
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'compressor',
    'djcelery',
    'guardian',
    'reversion',
    'sorl.thumbnail',

    'smartmin',
    'smartmin.csv_imports',
    'smartmin.users',

    'dash.orgs',
    'dash.utils',

    'tracpro.contacts',
    'tracpro.groups',
    'tracpro.home',
    'tracpro.msgs',
    'tracpro.orgs_ext',
    'tracpro.polls',
    'tracpro.profiles',
]

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _("English")),
    ('fr', _("French")),
    ('es', _("Spanish")),
    ('ps', _("Pashto")),
    ('fa', _("Persian")),
]

LOCALE_PATHS = [
    os.path.join(PROJECT_ROOT, 'locale'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'httprouterthread': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

LOGIN_REDIRECT_URL = reverse_lazy('home.home')

LOGIN_URL = reverse_lazy('users.user_login')

LOGOUT_REDIRECT_URL = reverse_lazy('home.home')

LOGOUT_URL = reverse_lazy('users.user_logout')

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'public', 'media')

MEDIA_URL = "/media/"

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'smartmin.middleware.AjaxRedirect',
    'dash.orgs.middleware.SetOrgMiddleware',
    'tracpro.profiles.middleware.ForcePasswordChangeMiddleware',
    'tracpro.groups.middleware.UserRegionsMiddleware',
)

ROOT_URLCONF = 'tracpro.urls'

SITE_DATE_FORMAT = r'%b %d, %Y'

SITE_ID = 1

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'tracpro', 'static'),
)

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'public', 'static')

STATIC_URL = '/sitestatic/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'dash.orgs.context_processors.user_group_perms_processor',
    'dash.orgs.context_processors.set_org_processor',
    'dash.context_processors.lang_direction',
    'tracpro.orgs_ext.views.org_ext_context_processor',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'tracpro', 'templates'),
)

TEMPLATE_LOADERS = (
    'hamlpy.template.loaders.HamlPyFilesystemLoader',
    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TIME_ZONE = 'GMT'

USER_TIME_ZONE = 'GMT'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# === Third-party settings. === #

ANONYMOUS_USER_ID = -1

BROKER_URL = CELERY_RESULT_BACKEND = 'redis://localhost:6379/4'

CELERYBEAT_SCHEDULE = {
    'sync-contacts': {
        'task': 'tracpro.contacts.tasks.sync_all_contacts',
        'schedule': datetime.timedelta(minutes=5),
        'args': ()
    },
    'fetch-runs': {
        'task': 'tracpro.polls.tasks.fetch_all_runs',
        'schedule': datetime.timedelta(minutes=5),
        'args': ()
    },
    'fetch-inbox-messages': {
        'task': 'tracpro.msgs.tasks.fetch_all_inbox_messages',
        'schedule': datetime.timedelta(minutes=5),
        'args': ()
    }
}

CELERY_TIMEZONE = 'UTC'

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'tracpro.compress.LessFilter'),
)

DEFAULT_LANGUAGE = 'en'

GROUP_PERMISSIONS = {
    "Administrators": (
        'orgs.org_home',
        'orgs.org_edit',
        'contacts.contact.*',
        'groups.group.*',
        'groups.region.*',
        'msgs.message.*',
        'msgs.inboxmessage.*',
        'polls.poll.*',
        'polls.pollrun.*',
        'polls.response.*',
        'profiles.profile.*',
    ),
    "Editors": (
        'contacts.contact.*',
        'groups.group_most_active',
        'groups.region_most_active',
        'msgs.message_send',
        'msgs.message_by_contact',
        'polls.poll_read',
        'polls.pollrun_create',
        'polls.pollrun_restart',
        'polls.pollrun_read',
        'polls.pollrun_participation',
        'polls.pollrun_latest',
        'polls.pollrun_list',
        'polls.pollrun_by_poll',
        'polls.response_by_contact',
        'polls.response_by_pollrun',
        'profiles.profile_user_read',
    ),
}

ORG_CONFIG_FIELDS = [{
    'name': 'facility_code_field',
    'field': {
        'help_text': _("Contact field to use as the facility code"),
        'required': True,
    }
}]

PERMISSIONS = {
    '*': (
        'create',  # can create an object
        'read',  # can view an object's details
        'update',  # can update an object
        'delete',  # can delete an object
        'list',  # can view a list of the objects
    ),
    'orgs.org': ('create', 'update', 'list', 'edit', 'home'),
    'contacts.contact': ('create', 'read', 'update', 'delete', 'list'),
    'groups.group': ('list', 'most_active', 'select'),
    'groups.region': ('list', 'most_active', 'select'),
    'msgs.message': ('list', 'send', 'by_contact'),
    'msgs.inboxmessage': ('read', 'list', 'conversation'),
    'polls.poll': ('read', 'update', 'list', 'select'),
    'polls.pollrun': ('create', 'restart', 'read', 'participation', 'list', 'by_poll', 'latest'),
    'polls.response': ('by_pollrun', 'by_contact'),
    # can't create profiles.user.* permissions because we don't own User
    'profiles.profile': ('user_create', 'user_read', 'user_update', 'user_list'),
}

RTL_LANGUAGES = ['ps', 'fa']

SITE_ALLOW_NO_ORG = (
    'orgs_ext.org_create',
    'orgs_ext.org_update',
    'orgs_ext.org_list',
    'profiles.admin_create',
    'profiles.admin_update',
    'profiles.admin_list',
)

SITE_API_HOST = 'rapidpro.io'

SITE_API_USER_AGENT = 'tracpro/1.0'

SITE_CHOOSER_URL_NAME = 'orgs_ext.org_chooser'

SITE_CHOOSER_TEMPLATE = 'org_chooser.haml'

SITE_HOST_PATTERN = 'http://%s.localhost:8000'

SITE_USER_HOME = '/'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
