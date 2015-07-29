from __future__ import absolute_import, unicode_literals

from .views import MessageCRUDL, InboxMessageCRUDL

urlpatterns = MessageCRUDL().as_urlpatterns()
urlpatterns += InboxMessageCRUDL().as_urlpatterns()