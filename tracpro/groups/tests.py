from __future__ import absolute_import, unicode_literals

from tracpro.groups.models import Region, Group
from tracpro.test import TracProTest


class RegionTest(TracProTest):
    def test_create(self):
        region = Region.create(self.unicef, "Zabul", 'R-101')
        self.assertEqual(region.org, self.unicef)
        self.assertEqual(region.name, "Zabul")
        self.assertEqual(region.uuid, 'R-101')


class GroupTest(TracProTest):
    def test_create(self):
        group = Group.create(self.unicef, "Male Teachers", 'R-101')
        self.assertEqual(group.org, self.unicef)
        self.assertEqual(group.name, "Male Teachers")
        self.assertEqual(group.uuid, 'R-101')