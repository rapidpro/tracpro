import factory.fuzzy
import factory.django


class FuzzyEmail(factory.fuzzy.FuzzyText):

    def fuzz(self):
        return super(FuzzyEmail, self).fuzz() + "@example.com"


class SmartModelFactory(factory.django.DjangoModelFactory):
    created_by = factory.SubFactory("tracpro.test.factories.User")
    modified_by = factory.SubFactory("tracpro.test.factories.User")

    class Meta:
        abstract = True
