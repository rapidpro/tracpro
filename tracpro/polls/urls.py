from __future__ import absolute_import, unicode_literals

from .views import PollCRUDL, IssueCRUDL, ResponseCRUDL

urlpatterns = PollCRUDL().as_urlpatterns()
urlpatterns += IssueCRUDL().as_urlpatterns()
urlpatterns += ResponseCRUDL().as_urlpatterns()
