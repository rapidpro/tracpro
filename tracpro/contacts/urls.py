from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from tracpro.utils import is_production
from .views import ContactCRUDL, force_contacts_sync

urlpatterns = ContactCRUDL().as_urlpatterns()

if not is_production():
    urlpatterns += [
        url(r'^force_contacts_sync/$', force_contacts_sync, name='force_contacts_sync'),
    ]
