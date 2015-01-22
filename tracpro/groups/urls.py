from __future__ import absolute_import, unicode_literals

from .views import GroupCRUDL, RegionCRUDL

urlpatterns = GroupCRUDL().as_urlpatterns()
urlpatterns += RegionCRUDL().as_urlpatterns()
