import factory
import factory.django
import factory.fuzzy

from tracpro.test.factory_utils import FuzzyUUID

from .. import models


__all__ = ['Region']


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
