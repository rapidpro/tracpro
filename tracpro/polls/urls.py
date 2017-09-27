from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from tracpro.utils import is_production
from .views import PollCRUDL, PollRunCRUDL, ResponseCRUDL, force_runs_sync

urlpatterns = PollCRUDL().as_urlpatterns()
urlpatterns += PollRunCRUDL().as_urlpatterns()
urlpatterns += ResponseCRUDL().as_urlpatterns()

if not is_production():
    urlpatterns += [
        url(r'^force_runs_sync/$', force_runs_sync, name='force_runs_sync'),
    ]
