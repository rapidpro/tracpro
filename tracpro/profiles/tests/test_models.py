from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User

from tracpro.test.cases import TracProDataTest


class UserPatchTest(TracProDataTest):

    def test_create_user(self):
        user = User.create(self.unicef, "Mo Polls", "mo@trac.com", "Qwerty123", False,
                           regions=[self.region1, self.region2])
        self.assertEqual(user.profile.full_name, "Mo Polls")

        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "mo@trac.com")
        self.assertEqual(user.get_full_name(), "Mo Polls")
        self.assertIsNotNone(user.password)
        self.assertFalse(user.profile.change_password)

        self.assertEqual(user.regions.count(), 2)
        self.assertEqual(user.get_regions(self.unicef).count(), 2)

        self.assertTrue(user.has_region_access(self.region1))
        self.assertTrue(user.has_region_access(self.region2))
        self.assertFalse(user.has_region_access(self.region3))
        self.assertFalse(user.has_region_access(self.region4))

    def test_has_profile(self):
        self.assertFalse(self.superuser.has_profile())
        self.assertTrue(self.admin.has_profile())
        self.assertTrue(self.user1.has_profile())

    def test_get_full_name(self):
        self.assertEqual(self.superuser.get_full_name(), "")
        self.assertEqual(self.admin.get_full_name(), "Richard")
        self.assertEqual(self.user1.get_full_name(), "Sam Sims")

    def test_is_admin_for(self):
        self.assertTrue(self.admin.is_admin_for(self.unicef))
        self.assertFalse(self.admin.is_admin_for(self.nyaruka))
        self.assertFalse(self.user1.is_admin_for(self.unicef))

    def test_str(self):
        self.assertEqual(str(self.superuser), "root")

        self.assertEqual(str(self.user1), "Sam Sims")
        self.user1.profile.full_name = None
        self.user1.profile.save()
        self.assertEqual(str(self.user1), "sam@unicef.org")
