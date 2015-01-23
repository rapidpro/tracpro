from __future__ import absolute_import, unicode_literals

from .views import PollCRUDL, QuestionCRUDL

urlpatterns = PollCRUDL().as_urlpatterns()
urlpatterns += QuestionCRUDL().as_urlpatterns()
