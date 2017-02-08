from __future__ import unicode_literals

import datetime

import factory
import factory.fuzzy

from temba_client.v2 import types

from tracpro.polls.models import FlowDefinition, RuleSet
from .factory_utils import FuzzyUUID


__all__ = ['TembaFlow', 'TembaFlowDefinition', 'TembaRuleSet', 'TembaBoundary', 'TembaExport']


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
    # participants = 0  # Removed in API v2
    runs = 0
    # completed_runs = 0  # Removed in API v2
    # rulesets = []  # Removed in API v2
    created_on = factory.LazyAttribute(lambda o: datetime.datetime.now())

    class Meta:
        model = types.Flow


class TembaFlowDefinition(TembaObjectFactory):
    rule_sets = []

    class Meta:
        model = FlowDefinition


class TembaRuleSet(TembaObjectFactory):
    uuid = FuzzyUUID()
    label = factory.fuzzy.FuzzyText()
    response_type = factory.fuzzy.FuzzyChoice(['C', 'O', 'N'])

    class Meta:
        model = RuleSet


class TembaGeometry(TembaObjectFactory):
    type = factory.fuzzy.FuzzyText()
    coordinates = factory.fuzzy.FuzzyText()

    class Meta:
        model = types.Boundary.Geometry


class TembaBoundary(TembaObjectFactory):
    osm_id = factory.fuzzy.FuzzyText(length=15)  # not a real UUID.
    name = factory.fuzzy.FuzzyText()
    level = 0
    parent = None
    geometry = factory.SubFactory(TembaGeometry)

    class Meta:
        model = types.Boundary


class TembaExport(TembaObjectFactory):
    version = 7
    flows = []
    campaigns = []
    triggers = []

    class Meta:
        model = types.Export
