from __future__ import absolute_import, unicode_literals

from .views import ContactCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
