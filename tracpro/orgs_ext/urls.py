from __future__ import unicode_literals

from . import views


urlpatterns = views.OrgExtCRUDL().as_urlpatterns()
