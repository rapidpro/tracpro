from __future__ import unicode_literals

import sys


if 'test' in sys.argv:
    from .tests import *  # noqa

else:
    from .dev import *  # noqa

    # django-debug-toolbar
    # INSTALLED_APPS.append('debug_toolbar')
