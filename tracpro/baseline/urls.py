from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import BaselineTermCRUDL

urlpatterns = BaselineTermCRUDL().as_urlpatterns()
