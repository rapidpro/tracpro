import factory
import factory.fuzzy

from tracpro.test.factory_utils import SmartModelFactory


__all__ = ['Org']


class Org(SmartModelFactory):
    name = factory.fuzzy.FuzzyText()
    language = "en"
    subdomain = factory.fuzzy.FuzzyText()
    api_token = factory.fuzzy.FuzzyText()

    class Meta:
        model = "orgs.Org"

    @factory.post_generation
    def available_languages(self, create, extracted, **kwargs):
        self.available_languages = extracted or ["en"]
        if create:
            self.save()
