from __future__ import unicode_literals

import factory
import factory.fuzzy

from tracpro.test.factory_utils import FuzzyEmail


__all__ = ['User']


class User(factory.django.DjangoModelFactory):
    username = factory.fuzzy.FuzzyText()
    email = FuzzyEmail()

    class Meta:
        model = "auth.User"

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or self.username
        self.set_password(password)
        if create:
            self.save()
