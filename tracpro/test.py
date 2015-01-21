from __future__ import unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.test import TestCase
from tracpro.groups.models import Group, Region
from uuid import uuid4


class TracProTest(TestCase):
    """
    Base class for all test cases in TracPro
    """
    def setUp(self):
        self.superuser = User.objects.create_superuser(username="root", email="super@user.com", password="root")

        self.unicef = self.create_org("UNICEF", timezone="Asia/Kabul", subdomain="unicef")
        self.nyaruka = self.create_org("Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka")

        self.region1 = self.create_region(self.unicef, name="Kandahar", uuid='G-001')
        self.region2 = self.create_region(self.unicef, name="Khost", uuid='G-002')
        self.region3 = self.create_region(self.unicef, name="Kunar", uuid='G-003')
        self.region4 = self.create_region(self.nyaruka, name="Kigali", uuid='G-004')

        self.group1 = self.create_group(self.unicef, name="Farmers", uuid='G-005')
        self.group2 = self.create_group(self.unicef, name="Teachers", uuid='G-006')
        self.group3 = self.create_group(self.unicef, name="Doctors", uuid='G-007')
        self.group4 = self.create_group(self.nyaruka, name="Programmers", uuid='G-008')

    def create_org(self, name, timezone, subdomain):
        return Org.objects.create(name=name, timezone=timezone, subdomain=subdomain, api_token=unicode(uuid4()),
                                  created_by=self.superuser, modified_by=self.superuser)

    def create_region(self, org, name, uuid):
        return Region.create(org, name, uuid)

    def create_group(self, org, name, uuid):
        return Group.create(org, name, uuid)

    def login(self, user):
        result = self.client.login(username=user.username, password=user.username)
        self.assertTrue(result, "Couldn't login as %(user)s / %(user)s" % dict(user=user.username))

    def url_get(self, subdomain, url, params=None):
        if params is None:
            params = {}
        extra = {}
        if subdomain:
            extra['HTTP_HOST'] = '%s.localhost' % subdomain
        return self.client.get(url, params, **extra)

    def url_post(self, subdomain, url, data=None):
        if data is None:
            data = {}
        extra = {}
        if subdomain:
            extra['HTTP_HOST'] = '%s.localhost' % subdomain
        return self.client.post(url, data, **extra)

    def assertLoginRedirect(self, response, subdomain, next):
        self.assertRedirects(response, 'http://%s.localhost/users/login/?next=%s' % (subdomain, next))
