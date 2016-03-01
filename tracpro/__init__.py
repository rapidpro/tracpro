from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app  # noqa


# NOTE: Version must be updated in docs/source/conf.py as well.
VERSION = (1, 1, 1, "dev")


def get_version(version):
    assert len(version) == 4, "Version must be formatted as (major, minor, micro, state)"

    major, minor, micro, state = version

    assert isinstance(major, int), "Major version must be an integer."
    assert isinstance(minor, int), "Minor version must be an integer."
    assert isinstance(micro, int), "Micro version must be an integer."
    assert state in ('final', 'dev'), "State must be either final or dev."

    if state == 'final':
        return "{}.{}.{}".format(major, minor, micro)
    else:
        return "{}.{}.{}.{}".format(major, minor, micro, state)


__version__ = get_version(VERSION)
