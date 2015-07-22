from __future__ import absolute_import, unicode_literals

from .views import PollCRUDL, PollRunCRUDL, ResponseCRUDL

urlpatterns = PollCRUDL().as_urlpatterns()
urlpatterns += PollRunCRUDL().as_urlpatterns()
urlpatterns += ResponseCRUDL().as_urlpatterns()
