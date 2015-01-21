from __future__ import absolute_import, unicode_literals

from .views import PollCRUDL

urlpatterns = PollCRUDL().as_urlpatterns()
