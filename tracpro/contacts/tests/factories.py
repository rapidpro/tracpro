import random

import factory
import factory.django
import factory.fuzzy

from tracpro.test import factory_utils

from .. import models


__all__ = ['Contact']


class Contact(factory_utils.SmartModelFactory):
    uuid = factory_utils.FuzzyUUID()
    org = factory.SubFactory("tracpro.test.factories.Org")
    urn = factory.Sequence(lambda n: random.choice(("twitter:contact", "tel:123")) + str(n))
    region = factory.SubFactory("tracpro.test.factories.Region")

    class Meta:
        model = models.Contact


class TwitterContact(Contact):
    urn = factory.Sequence(lambda n: "twitter:contact" + str(n))


class PhoneContact(Contact):
    urn = factory.Sequence(lambda n: "tel:123" + str(n))
