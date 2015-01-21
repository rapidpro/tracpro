from __future__ import absolute_import, unicode_literals

from smartmin.views import SmartCRUDL
from .models import Poll


class PollCRUDL(SmartCRUDL):
    model_name = Poll
    actions = ()