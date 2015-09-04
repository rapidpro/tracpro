from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views


urlpatterns = views.GroupCRUDL().as_urlpatterns()
urlpatterns += views.RegionCRUDL().as_urlpatterns()
urlpatterns += [
    url("^toggle-subregions/$",
        views.ToggleSubregions.as_view(),
        name="toggle-subregions"),
]
