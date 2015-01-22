from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, url
from .views import ContactCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()

# contact create view can optionally be accessed with an initial region id
urlpatterns += patterns('', url(r'^contact/create/(?P<region>\d+)/$',
                                ContactCRUDL.Create.as_view(),
                                name='contacts.contact_create_in'))