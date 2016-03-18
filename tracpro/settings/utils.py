from __future__ import unicode_literals

import os

from django.conf import global_settings as django_defaults
from django.core.exceptions import ImproperlyConfigured


def from_env(variable, default=None):
    """Return the variable from the environment, falling back to a default."""
    return os.environ.get(variable, default)


def from_env_or_django(variable):
    """Return the variable from the environment, falling back to the Django default."""
    return from_env(variable, getattr(django_defaults, variable))


def require_env(*variables):
    """Raise ImproperlyConfigured unless the variable is in the environment."""
    for variable in variables:
        if variable not in os.environ:
            raise ImproperlyConfigured(
                "{} must be defined in the environment.".format(variable))
