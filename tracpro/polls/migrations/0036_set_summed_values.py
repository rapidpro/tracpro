# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from django.db import migrations
from django.db.models import F

from tracpro.polls.models import SAMEDAY_SUM, SAMEDAY_LAST


def forward(apps, schema):
    Answer = apps.get_model('polls.Answer')
    Org = apps.get_model('orgs.Org')

    # Initialize summed_value to value
    Answer.objects.update(value_to_use=F('value'))

    for org in Org.objects.all():
        config = json.loads(org.config)
        how_to_handle = config.get('how_to_handle_sameday_responses', SAMEDAY_LAST)
        if how_to_handle == SAMEDAY_SUM:
            # We don't handle existing orgs already set to SAMEDAY_SUM -
            # There should not be any, but
            # just to avoid misleading someone if they're migrating forward
            # and back or something:
            raise Exception("Don't try to run this migration with any orgs set to sum same-day responses (org=%s)" % org)


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0035_auto_20170915_1615'),
        ('orgs', '0017_auto_20161026_1513'),
    ]

    operations = [
        migrations.RunPython(
            forward,
            migrations.RunPython.noop
        )
    ]
