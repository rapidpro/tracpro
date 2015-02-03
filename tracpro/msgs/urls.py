from __future__ import absolute_import, unicode_literals

from .views import MessageCRUDL

urlpatterns = MessageCRUDL().as_urlpatterns()
