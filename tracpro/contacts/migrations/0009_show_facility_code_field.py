# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models, migrations


def show_facility_code_field(apps, schema_editor):
    """Create a facility code Field for each active org."""
    Org = apps.get_model('orgs', 'Org')
    DataField = apps.get_model('contacts', 'DataField')

    for org in Org.objects.filter(is_active=True):
        # Must manually load config; get_config is not available.
        config = json.loads(org.config) if org.config else {}
        DataField.objects.create(
            org=org,
            key=config.pop("facility_code_field", "facility_code"),
            value_type="T",  # Text
            show_on_tracpro=True,
        )

        # Save the config without `facility_code_field`, which is no longer
        # in use.
        org.config = json.dumps(config) if config else None
        org.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0008_add_contactfield_model'),
    ]

    operations = [
        migrations.RunPython(
            show_facility_code_field, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='contact',
            name='facility_code',
        ),
    ]
