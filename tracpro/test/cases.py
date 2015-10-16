from __future__ import unicode_literals

import datetime
from uuid import uuid4

import pytz
import redis

from dash.orgs.models import Org

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from tracpro.groups.models import Group, Region
from tracpro.polls.models import Question

from . import factories


class TracProTest(TestCase):
    """Base class for all test cases in TracPro."""

    def setUp(self):
        super(TracProTest, self).setUp()
        self.clear_cache()

    def clear_cache(self):
        # we are extra paranoid here and actually hardcode redis to 'localhost'
        # and '10' Redis 10 is our testing redis db
        r = redis.StrictRedis(host='localhost', db=10)
        r.flushdb()

    def create_org(self, name, timezone, subdomain):
        org = Org.objects.create(
            name=name, timezone=timezone, subdomain=subdomain,
            api_token=str(uuid4()), created_by=self.superuser,
            modified_by=self.superuser)
        return org

    def create_region(self, org, name, uuid):
        return Region.create(org, name, uuid)

    def create_group(self, org, name, uuid):
        return Group.create(org, name, uuid)

    def create_admin(self, org, full_name, email):
        user = User.create(
            None, full_name, email, password=email, change_password=False)
        user.org_admins.add(org)
        return user

    def create_user(self, org, full_name, email, regions):
        return User.create(
            org, full_name, email, password=email, change_password=False,
            regions=regions)

    def create_contact(self, org, name, urn, region, group, uuid):
        user = org.administrators.first()
        return factories.Contact(
            org=org, name=name, urn=urn, region=region, group=group, uuid=uuid,
            language='eng', created_by=user, modified_by=user)

    def login(self, user):
        result = self.client.login(username=user.username, password=user.username)
        self.assertTrue(
            result, "Couldn't login as %(user)s / %(user)s" % dict(user=user.username))

    def switch_region(self, region):
        session = self.client.session
        key = '{org}:region_id'.format(org=region.org.pk)
        session[key] = region.pk
        session.save()

    def url_get(self, subdomain, url, params=None, **extra):
        if subdomain:
            extra.setdefault('HTTP_HOST', "{}.testserver".format(subdomain))
        return self.client.get(url, params, **extra)

    def url_post(self, subdomain, url, data=None, **extra):
        if subdomain:
            extra.setdefault('HTTP_HOST', "{}.testserver".format(subdomain))
        return self.client.post(url, data, **extra)

    def datetime(self, year, month, day, hour=0, minute=0, second=0,
                 microsecond=0, tz=pytz.UTC):
        return datetime.datetime(year, month, day,
                                 hour, minute, second, microsecond, tz)

    def assertRedirects(self, response, url, subdomain=None, **kwargs):
        if subdomain:
            kwargs.setdefault('host', '{}.testserver'.format(subdomain))
        return super(TracProTest, self).assertRedirects(response, url, **kwargs)

    def assertLoginRedirect(self, response, subdomain, next_url):
        url = '{}?next={}'.format(reverse('users.user_login'), next_url)
        self.assertRedirects(response, url, subdomain)


class TracProDataTest(TracProTest):
    """Common data set-up."""

    def setUp(self):
        super(TracProDataTest, self).setUp()

        self.superuser = User.objects.create_superuser(
            username="root", email="super@user.com", password="root")

        # some orgs
        self.unicef = self.create_org(
            "UNICEF", timezone="Asia/Kabul", subdomain="unicef")
        self.nyaruka = self.create_org(
            "Nyaruka", timezone="Africa/Kigali", subdomain="nyaruka")

        # some admins for those orgs
        self.admin = self.create_admin(self.unicef, "Richard", "admin@unicef.org")
        self.eric = self.create_admin(self.nyaruka, "Eric", "eric@nyaruka.com")

        # some regions
        self.region1 = self.create_region(self.unicef, name="Kandahar", uuid='G-001')
        self.region2 = self.create_region(self.unicef, name="Khost", uuid='G-002')
        self.region3 = self.create_region(self.unicef, name="Kunar", uuid='G-003')
        self.region4 = self.create_region(self.nyaruka, name="Kigali", uuid='G-004')

        # some users in those regions
        self.user1 = self.create_user(
            self.unicef, "Sam Sims", "sam@unicef.org", regions=[self.region1])
        self.user2 = self.create_user(
            self.unicef, "Sue", "sue@unicef.org", regions=[self.region2, self.region3])
        self.user3 = self.create_user(
            self.nyaruka, "Nic", "nic@nyaruka.com", regions=[self.region4])

        # some reporting groups
        self.group1 = self.create_group(self.unicef, name="Farmers", uuid='G-005')
        self.group2 = self.create_group(self.unicef, name="Teachers", uuid='G-006')
        self.group3 = self.create_group(self.unicef, name="Doctors", uuid='G-007')
        self.group4 = self.create_group(self.nyaruka, name="Programmers", uuid='G-008')

        # some contacts
        self.contact1 = self.create_contact(
            self.unicef, "Ann", 'tel:1234', self.region1, self.group1, 'C-001')
        self.contact2 = self.create_contact(
            self.unicef, "Bob", 'tel:2345', self.region1, self.group1, 'C-002')
        self.contact3 = self.create_contact(
            self.unicef, "Cat", 'tel:3456', self.region1, self.group2, 'C-003')
        self.contact4 = self.create_contact(
            self.unicef, "Dan", 'twitter:danny', self.region2, self.group2, 'C-004')
        self.contact5 = self.create_contact(
            self.unicef, "Eve", 'twitter:evee', self.region3, self.group3, 'C-005')
        self.contact6 = self.create_contact(
            self.nyaruka, "Norbert", 'twitter:n7', self.region4, self.group4, 'C-006')

        # a poll with some questions
        self.poll1 = factories.Poll(
            org=self.unicef, name="Farm Poll", flow_uuid='F-001')
        self.poll1_question1 = factories.Question(
            poll=self.poll1,
            type=Question.TYPE_NUMERIC,
            text="Number of sheep",
            order=1,
            ruleset_uuid='RS-001',
        )

        self.poll1_question2 = factories.Question(
            poll=self.poll1,
            type=Question.TYPE_OPEN,
            text="How is the weather?",
            order=2,
            ruleset_uuid='RS-002',
        )

        # and a poll for the other org
        self.poll2 = factories.Poll(
            org=self.nyaruka, name="Code Poll", flow_uuid='F-002')
        self.poll2_question1 = factories.Question(
            poll=self.poll2,
            type=Question.TYPE_NUMERIC,
            text="Number of bugs",
            order=1,
            ruleset_uuid='RS-003',
        )
