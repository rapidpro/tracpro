import factory
import factory.fuzzy

from tracpro.test.factory_utils import FuzzyUUID

from .. import models


__all__ = ['Region', 'Group', 'Boundary']


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


class Boundary(factory.django.DjangoModelFactory):
    org = factory.SubFactory("tracpro.test.factories.Org")
    rapidpro_uuid = factory.fuzzy.FuzzyText(length=15)  # not a real UUID.
    name = factory.fuzzy.FuzzyText()
    level = models.Boundary.LEVEL_COUNTRY
    parent = None
    geometry = ""

    class Meta:
        model = models.Boundary
