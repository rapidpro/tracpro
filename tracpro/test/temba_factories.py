from __future__ import unicode_literals

import datetime

import factory
import factory.fuzzy

from temba_client import types

from .factory_utils import FuzzyUUID


__all__ = ['TembaFlow', 'TembaRuleSet']


class TembaObjectFactory(factory.Factory):

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.create(*args, **kwargs)


class TembaFlow(TembaObjectFactory):
    uuid = FuzzyUUID()
    name = factory.fuzzy.FuzzyText()
    archived = False
    participants = 0
    runs = 0
    completed_runs = 0
    rulesets = []
    created_on = factory.LazyAttribute(lambda o: datetime.datetime.now())

    class Meta:
        model = types.Flow


class TembaRuleSet(TembaObjectFactory):
    uuid = FuzzyUUID()
    label = factory.fuzzy.FuzzyText()
    response_type = factory.fuzzy.FuzzyChoice(['C', 'O', 'N'])

    class Meta:
        model = types.RuleSet
