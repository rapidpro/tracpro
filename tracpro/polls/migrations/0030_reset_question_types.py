# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from temba_client.v2 import TembaClient

from django.conf import settings
from django.db import migrations

NUMERIC_TESTS = ('number', 'lt', 'eq', 'gt', 'between')


def get_temba_client(org):
    host = settings.SITE_API_HOST
    user_agent = settings.SITE_API_USER_AGENT
    return TembaClient(host=host, user_agent=user_agent, token=org.api_token)


def guess_question_type_from_rules(apps, schema_editor):
    """Guess question type from the tests applied to question input."""
    for org in apps.get_model('orgs', 'Org').objects.all():
        client = get_temba_client(org)
        for poll in org.polls.all():
            exports = client.get_definitions(flows=[poll.flow_uuid])
            rulesets = exports.flows[0].rule_sets
            rules_by_ruleset_uuid = {r['uuid']: r['rules'] for r in rulesets}
            for question in poll.questions.all():
                rules = rules_by_ruleset_uuid.get(question.ruleset_uuid)
                tests = [r['test']['type'] for r in rules] if rules else []
                tests = tests[:-1]  # The last test is always "Other"
                if not tests:
                    question.question_type = 'O'
                elif all(t in NUMERIC_TESTS for t in tests):
                    question.question_type = 'N'
                else:
                    question.question_type = 'C'
                question.save()


def set_question_type_from_response_type(apps, schema_editor):
    """Reset question type from ruleset response type."""
    for org in apps.get_model('orgs', 'Org').objects.all():
        client = get_temba_client(org)
        for poll in org.polls.all():
            rulesets = client.get_flow(poll.flow_uuid).rulesets
            rulesets_by_uuid = {r.uuid: r for r in rulesets}
            for question in poll.questions.all():
                ruleset = rulesets_by_uuid.get(question.ruleset_uuid)
                if ruleset:
                    question.question_type = ruleset.response_type
                    question.save()


class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0029_poll_tweaks'),
    ]

    operations = [
        migrations.RunPython(
            guess_question_type_from_rules,
            set_question_type_from_response_type),
    ]
