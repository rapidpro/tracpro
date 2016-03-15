from __future__ import unicode_literals

import factory
import factory.fuzzy

from tracpro.test.factory_utils import FuzzyUUID

from .. import models


__all__ = ['Region', 'Group']


class AbstractGroup(factory.django.DjangoModelFactory):
    uuid = FuzzyUUID()
    name = factory.fuzzy.FuzzyText()
    org = factory.SubFactory("tracpro.test.factories.Org")

    class Meta:
        abstract = True
        model = models.AbstractGroup


class Region(AbstractGroup):

    class Meta:
        model = models.Region


class Group(AbstractGroup):

    class Meta:
        model = models.Group
