import datetime
import json

import factory
import factory.fuzzy

from django.utils import timezone

from tracpro.test.factory_utils import FuzzyUUID

from .. import models


__all__ = [
    'Poll', 'PollRun', 'UniversalPollRun', 'RegionalPollRun',
    'PropagatedPollRun', 'Question', 'Answer', 'Response']


class Poll(factory.django.DjangoModelFactory):
    flow_uuid = FuzzyUUID()
    org = factory.SubFactory("tracpro.test.factories.Org")
    rapidpro_name = factory.LazyAttribute(lambda o: o.name)
    name = factory.fuzzy.FuzzyText()
    is_active = True

    class Meta:
        model = models.Poll


class PollRun(factory.django.DjangoModelFactory):
    create_method = "create"

    pollrun_type = factory.fuzzy.FuzzyChoice(c[0] for c in models.PollRun.TYPE_CHOICES)
    poll = factory.SubFactory('tracpro.test.factories.Poll')
    region = factory.SubFactory('tracpro.test.factories.Region')
    created_by = factory.SubFactory('tracpro.test.factories.User')
    conducted_on = factory.LazyAttribute(lambda o: timezone.now())

    class Meta:
        exclude = ['create_method']
        model = models.PollRun

    @factory.lazy_attribute
    def region(self):
        """Ensure that region and poll share the same org."""
        from tracpro.test import factories
        return factories.Region(org=self.poll.org)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create an instance of the model, and save it to the database."""
        manager = cls._get_manager(model_class)
        if cls._meta.django_get_or_create:
            return cls._get_or_create(model_class, *args, **kwargs)
        return getattr(manager, cls.create_method)(*args, **kwargs)


class RegionalPollRun(PollRun):
    create_method = "create_regional"

    pollrun_type = models.PollRun.TYPE_REGIONAL


class UniversalPollRun(PollRun):
    create_method = "get_or_create_universal"

    pollrun_type = models.PollRun.TYPE_UNIVERSAL
    region = None
    for_date = factory.LazyAttribute(lambda o: o.conducted_on)


class PropagatedPollRun(PollRun):
    create_method = "create_propagated"

    pollrun_type = models.PollRun.TYPE_PROPAGATED


class Question(factory.django.DjangoModelFactory):
    ruleset_uuid = FuzzyUUID()
    poll = factory.SubFactory('tracpro.test.factories.Poll')
    rapidpro_name = factory.LazyAttribute(lambda o: o.name)
    name = factory.fuzzy.FuzzyText()
    question_type = factory.fuzzy.FuzzyChoice(c[0] for c in models.Question.TYPE_CHOICES)
    order = factory.Sequence(lambda n: n)
    json_rules = factory.LazyAttribute(lambda o: json.dumps([]))

    class Meta:
        model = models.Question


class Answer(factory.django.DjangoModelFactory):
    response = factory.SubFactory('tracpro.test.factories.Response')
    question = factory.SubFactory('tracpro.test.factories.Question')
    value = factory.fuzzy.FuzzyText()
    category = factory.fuzzy.FuzzyText()
    submitted_on = factory.fuzzy.FuzzyDate(
        start_date=datetime.date.today() - datetime.timedelta(days=7),
        end_date=datetime.date.today())

    class Meta:
        model = models.Answer


class Response(factory.django.DjangoModelFactory):
    flow_run_id = factory.Sequence(lambda n: n)
    pollrun = factory.SubFactory('tracpro.test.factories.PollRun')
    contact = factory.SubFactory('tracpro.test.factories.Contact')
    created_on = factory.fuzzy.FuzzyDate(
        start_date=datetime.date.today() - datetime.timedelta(days=7),
        end_date=datetime.date.today())
    updated_on = factory.LazyAttribute(lambda o: o.created_on)
    status = factory.fuzzy.FuzzyChoice(c[0] for c in models.Response.STATUS_CHOICES)

    class Meta:
        model = models.Response
