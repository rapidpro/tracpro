from __future__ import absolute_import, unicode_literals

import datetime
import os
import sys

from django.utils.translation import ugettext_lazy as _

# ----------------------------------------------------------------------------
# Sets TESTING to True if this configuration is read during a unit test
# ----------------------------------------------------------------------------
TESTING = sys.argv[1:2] == ['test']

# Django settings for tns_glass project.
THUMBNAIL_DEBUG = False

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Nyaruka', 'code@nyaruka.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'tracpro.sqlite',                # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# set the mail settings, we send throught gmail
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'server@nyaruka.com'
DEFAULT_FROM_EMAIL = 'server@nyaruka.com'
EMAIL_HOST_PASSWORD = 'NOTREAL'
EMAIL_USE_TLS = True

SITE_API_HOST = 'http://localhost:8001/api/v1'
SITE_API_USER_AGENT = 'tracpro/1.0'
SITE_HOST_PATTERN = 'http://%s.localhost:8000'
SITE_CHOOSER_URL_NAME = 'orgs_ext.org_chooser'
SITE_CHOOSER_TEMPLATE = 'org_chooser.haml'
SITE_USER_HOME = '/'
SITE_ALLOW_NO_ORG = ('orgs_ext.org_create', 'orgs_ext.org_update', 'orgs_ext.org_list',
                     'profiles.admin_create', 'profiles.admin_update', 'profiles.admin_list')

# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone
TIME_ZONE = 'GMT'
USER_TIME_ZONE = 'GMT'
USE_TZ = True

SITE_DATE_FORMAT = r'%b %d, %Y'

MODELTRANSLATION_TRANSLATION_REGISTRY = "translation"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# Available languages for translation
LANGUAGES = (('en', _("English")), ('fr', _("French")), ('es', _("Spanish")), ('ps', _("Pashto")), ('fa', _("Persian")))
RTL_LANGUAGES = {'ps', 'fa'}
DEFAULT_LANGUAGE = "en"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/sitestatic/'
COMPRESS_URL = '/sitestatic/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/sitestatic/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'tracpro.compress.LessFilter'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'Q#9JgQuBlOvUt#Y*LuduDO6L#JrWQ%hRT3*6ALdcPHNQWLqXaiMHy6jSC6$&Chx2Zab38wO&tBg@'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'hamlpy.template.loaders.HamlPyFilesystemLoader',
    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'dash.orgs.middleware.SetOrgMiddleware',
    'tracpro.profiles.middleware.ForcePasswordChangeMiddleware',
    'tracpro.groups.middleware.UserRegionsMiddleware'
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
    'tracpro.orgs_ext.views.org_ext_context_processor'
)

ROOT_URLCONF = 'tracpro.urls'

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:10',
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
        }
    }
}

ORG_CONFIG_FIELDS = [dict(name='facility_code_field',
                          field=dict(help_text=_("Contact field to use as the facility code"), required=True))]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # mo-betta permission management
    'guardian',

    # versioning of our data
    'reversion',

    # the django admin
    'django.contrib.admin',

    # compress our CSS and js
    'compressor',

    # thumbnail
    'sorl.thumbnail',

    # smartmin
    'smartmin',

    # import tasks
    'smartmin.csv_imports',

    # users
    'smartmin.users',

    # async tasks,
    'djcelery',

    # dash apps
    'dash.orgs',
    'dash.utils',

    # custom
    'tracpro.contacts',
    'tracpro.groups',
    'tracpro.home',
    'tracpro.msgs',
    'tracpro.orgs_ext',
    'tracpro.polls',
    'tracpro.profiles',
)

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

# ----------------------------------------------------------------------------
# Directory Configuration
# ----------------------------------------------------------------------------

PROJECT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)))
RESOURCES_DIR = os.path.join(PROJECT_DIR, '../resources')

LOCALE_PATHS = (os.path.join(PROJECT_DIR, '../locale'),)
RESOURCES_DIR = os.path.join(PROJECT_DIR, '../resources')
FIXTURE_DIRS = (os.path.join(PROJECT_DIR, '../fixtures'),)
TESTFILES_DIR = os.path.join(PROJECT_DIR, '../testfiles')
TEMPLATE_DIRS = (os.path.join(PROJECT_DIR, '../templates'),)
STATICFILES_DIRS = (os.path.join(PROJECT_DIR, '../static'), os.path.join(PROJECT_DIR, '../media'), )
STATIC_ROOT = os.path.join(PROJECT_DIR, '../sitestatic')
MEDIA_ROOT = os.path.join(PROJECT_DIR, '../media')
MEDIA_URL = "/media/"

# ----------------------------------------------------------------------------
# Permission Management
# ----------------------------------------------------------------------------

# this lets us easily create new permissions across our objects
PERMISSIONS = {
    '*': ('create',  # can create an object
          'read',   # can read an object, viewing it's details
          'update',  # can update an object
          'delete',  # can delete an object,
          'list'),  # can view a list of the objects

    'orgs.org': ('create', 'update', 'list', 'edit', 'home'),

    'contacts.contact': ('create', 'read', 'update', 'delete', 'list'),

    'groups.group': ('list', 'most_active', 'select'),

    'groups.region': ('list', 'most_active', 'select'),

    'msgs.message': ('list', 'send', 'by_contact'),

    'polls.poll': ('read', 'update', 'list', 'select'),

    'polls.issue': ('create', 'restart', 'read', 'participation', 'list', 'by_poll', 'latest'),

    'polls.response': ('by_issue', 'by_contact'),

    # can't create profiles.user.* permissions because we don't own User
    'profiles.profile': ('user_create', 'user_read', 'user_update', 'user_list'),
}

# assigns the permissions that each group should have
GROUP_PERMISSIONS = {
    "Administrators": (
        'orgs.org_home',
        'orgs.org_edit',

        'contacts.contact.*',
        'groups.group.*',
        'groups.region.*',
        'msgs.message.*',
        'polls.poll.*',
        'polls.issue.*',
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
        'polls.issue_create',
        'polls.issue_restart',
        'polls.issue_read',
        'polls.issue_participation',
        'polls.issue_latest',
        'polls.issue_list',
        'polls.issue_by_poll',
        'polls.response_by_contact',
        'polls.response_by_issue',
        'profiles.profile_user_read',
    ),
}

# ----------------------------------------------------------------------------
# Login / Logout
# ----------------------------------------------------------------------------
LOGIN_URL = "/users/login/"
LOGOUT_URL = "/users/logout/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ----------------------------------------------------------------------------
# Guardian Configuration
# ----------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ANONYMOUS_USER_ID = -1

# ----------------------------------------------------------------------------
# Django-Nose config
# ----------------------------------------------------------------------------

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SOUTH_TESTS_MIGRATE = False

# ----------------------------------------------------------------------------
# Debug Toolbar
# ----------------------------------------------------------------------------

INTERNAL_IPS = ('127.0.0.1',)

# ----------------------------------------------------------------------------
# Django-celery
# ----------------------------------------------------------------------------
import djcelery  # noqa

djcelery.setup_loader()

BROKER_URL = 'redis://localhost:6379/%d' % (10 if TESTING else 4)
CELERY_RESULT_BACKEND = BROKER_URL

CELERYBEAT_SCHEDULE = {
    'sync-contacts': {
        'task': 'tracpro.contacts.tasks.sync_all_contacts',
        'schedule': datetime.timedelta(minutes=30),
        'args': ()
    },
    'fetch-runs': {
        'task': 'tracpro.polls.tasks.fetch_all_runs',
        'schedule': datetime.timedelta(minutes=5),
        'args': ()
    }
}

CELERY_TIMEZONE = 'UTC'
