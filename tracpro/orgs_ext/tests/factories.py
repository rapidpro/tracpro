import factory
import factory.django
import factory.fuzzy

from dash.orgs import models


class SmartModelFactory(factory.django.DjangoModelFactory):
    created_by = factory.SubFactory("tracpro.orgs_ext.tests.factories.User")
    modified_by = factory.SubFactory("tracpro.orgs_ext.tests.factories.User")

    class Meta:
        abstract = True


class User(factory.django.DjangoModelFactory):
    username = factory.fuzzy.FuzzyText()
    email = factory.Sequence(lambda n: "user{0}@gmail.com".format(n))

    class Meta:
        model = "auth.User"

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "password"
        self.set_password(password)
        if create:
            self.save()


class Org(SmartModelFactory):
    name = factory.fuzzy.FuzzyText()
    language = "en"

    class Meta:
        model = "orgs.Org"

    @factory.post_generation
    def available_languages(self, create, extracted, **kwargs):
        self.available_languages = extracted or ["en"]
        if create:
            self.save()
