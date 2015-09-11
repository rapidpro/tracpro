from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from ..middleware import UserRegionsMiddleware
from ..models import Region


class TestUserRegionsMiddleware(TracProTest):

    def setUp(self):
        super(TestUserRegionsMiddleware, self).setUp()
        self.middleware = UserRegionsMiddleware()
        self.org = factories.Org()
        self.user = factories.User()

    def get_request(self, **kwargs):
        request_kwargs = {'HTTP_HOST': "{}.testserver".format(self.org.subdomain)}
        request = RequestFactory().get("/", **request_kwargs)
        for key, value in kwargs.items():
            setattr(request, key, value)
        return request

    def make_regions(self):
        """Create a collection of nested regions."""
        self.region_uganda = factories.Region(
            org=self.org, name="Uganda")
        self.region_kampala = factories.Region(
            org=self.org, name="Kampala", parent=self.region_uganda)
        self.region_makerere = factories.Region(
            org=self.org, name="Makerere", parent=self.region_kampala)
        self.region_entebbe = factories.Region(
            org=self.org, name="Entebbe", parent=self.region_uganda)
        self.region_kenya = factories.Region(
            org=self.org, name="Kenya")
        self.region_nairobi = factories.Region(
            org=self.org, name="Nairobi", parent=self.region_kenya)
        self.region_mombasa = factories.Region(
            org=self.org, name="Mombasa", parent=self.region_kenya)

        self.region_inactive = factories.Region(
            org=self.org, name="Inactive", parent=self.region_nairobi,
            is_active=False)

        return Region.get_all(self.org)

    def test_variables_set(self):
        """Middleware should set several commonly-used region variables."""
        request = self.get_request(user=self.user, org=self.org, session={})
        self.middleware.process_request(request)
        self.assertTrue(hasattr(request, 'region'))
        self.assertTrue(hasattr(request, 'include_subregions'))
        self.assertTrue(hasattr(request, 'user_regions'))
        self.assertTrue(hasattr(request, 'data_regions'))

    def test_user_regions__unauthenticated(self):
        """User regions should be set to null for unauthenticated users."""
        request = self.get_request(user=AnonymousUser(), org=self.org)
        self.middleware.set_user_regions(request)
        self.assertIsNone(request.user_regions)

    def test_user_regions__no_org(self):
        """User regions should be set to null for non-org views."""
        request = self.get_request(user=self.user, org=None)
        self.middleware.set_user_regions(request)
        self.assertIsNone(request.user_regions)

    def test_user_regions(self):
        """User regions should be set to the value of get_all_regions."""
        self.make_regions()
        self.region_kenya.users.add(self.user)
        request = self.get_request(user=self.user, org=self.org)
        self.middleware.set_user_regions(request)
        self.assertEqual(
            set(request.user_regions),
            set([self.region_kenya, self.region_nairobi, self.region_mombasa]))

    def test_include_subregions__default(self):
        """If key is not in the session, should default to True."""
        request = self.get_request(session={})
        self.middleware.set_include_subregions(request)
        self.assertTrue(request.include_subregions)

    def test_include_subregions__yes(self):
        """include_subregions should be retrieved from the session."""
        request = self.get_request(session={'include_subregions': True})
        self.middleware.set_include_subregions(request)
        self.assertTrue(request.include_subregions)

    def test_include_subregions__no(self):
        """include_subregions should be retrieved from the session."""
        request = self.get_request(session={'include_subregions': False})
        self.middleware.set_include_subregions(request)
        self.assertFalse(request.include_subregions)

    def test_data_regions__no_region(self):
        """If there is no current region, data_regions should be None."""
        request = self.get_request(user=self.user, region=None)
        self.middleware.set_data_regions(request)
        self.assertIsNone(request.data_regions)

    def test_data_regions__include_subregions(self):
        """Include all subregions user has access to if include_subregions is True."""
        self.make_regions()
        user_regions = Region.objects.filter(pk__in=(
            self.region_uganda.pk, self.region_kenya.pk, self.region_nairobi.pk))
        request = self.get_request(
            user=self.user, region=self.region_kenya, include_subregions=True,
            user_regions=user_regions)
        self.middleware.set_data_regions(request)
        self.assertEqual(
            set(request.data_regions),
            set([self.region_kenya, self.region_nairobi]))

    def test_data_regions__exclude_subregions(self):
        """Include only the current region if include_subregions is False."""
        self.make_regions()
        user_regions = Region.objects.filter(pk__in=(
            self.region_uganda.pk, self.region_kenya.pk, self.region_nairobi.pk))
        request = self.get_request(
            user=self.user, region=self.region_kenya, include_subregions=False,
            user_regions=user_regions)
        self.middleware.set_data_regions(request)
        self.assertEqual(
            set(request.data_regions),
            set([self.region_kenya]))

    def test_region__unauthenticated(self):
        """Current region should be None for an unauthenticated user."""
        request = self.get_request(user=AnonymousUser(), org=self.org)
        self.middleware.set_region(request)
        self.assertIsNone(request.region)

    def test_region__no_org(self):
        """Current region should be None if there is no current org."""
        request = self.get_request(user=self.user, org=None)
        self.middleware.set_region(request)
        self.assertIsNone(request.region)

    def test_region__not_set__admin(self):
        """If region_id is not in the session, admin will see All Regions."""
        self.make_regions()
        self.org.administrators.add(self.user)
        user_regions = Region.objects.filter(pk__in=(
            self.region_uganda.pk, self.region_kenya.pk, self.region_nairobi.pk))
        request = self.get_request(
            user=self.user, org=self.org, session={}, user_regions=user_regions)
        self.middleware.set_region(request)
        self.assertIsNone(request.region)

    def test_region__not_set(self):
        """If region_id is not in the session, user will see first of their regions."""
        self.make_regions()
        user_regions = Region.objects.filter(pk=self.region_kenya.pk)
        request = self.get_request(
            user=self.user, org=self.org, session={}, user_regions=user_regions)
        self.middleware.set_region(request)
        self.assertEqual(request.region, self.region_kenya)

    def test_region__not_in_user_regions(self):
        """If region is not in user regions, return the first of the user's regions."""
        self.make_regions()
        user_regions = Region.objects.filter(pk=self.region_kenya.pk)
        request = self.get_request(
            user=self.user, org=self.org, session={'region_id': self.region_nairobi.pk},
            user_regions=user_regions)
        self.middleware.set_region(request)
        self.assertEqual(request.region, self.region_kenya)

    def test_region(self):
        self.make_regions()
        user_regions = Region.objects.filter(pk=self.region_kenya.pk)
        request = self.get_request(
            user=self.user, org=self.org, session={'region_id': self.region_kenya.pk},
            user_regions=user_regions)
        self.middleware.set_region(request)
        self.assertEqual(request.region, self.region_kenya)
