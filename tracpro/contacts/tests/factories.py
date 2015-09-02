import factory
import factory.django
import factory.fuzzy

from tracpro.test import factory_utils

from .. import models


__all__ = ['Contact']


class Contact(factory_utils.SmartModelFactory):
    uuid = factory_utils.FuzzyUUID()
    org = factory.SubFactory("tracpro.test.factories.Org")
    urn = factory.fuzzy.FuzzyText()
    region = factory.SubFactory("tracpro.test.factories.Region")

    class Meta:
        model = models.Contact
