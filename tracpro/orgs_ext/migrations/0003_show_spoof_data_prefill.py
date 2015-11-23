# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf import settings
from django.db import models, migrations


def add_show_spoof_data(apps, schema_editor):
    """Set default for show spoof data to False"""
    for org in apps.get_model('orgs', 'Org').objects.all():
        config = json.loads(org.config) if org.config else {}
        # Default Caktus to show spoof data = True for testing
        if org.name.lower() == 'caktus':
            config['show_spoof_data'] = True
            org.config = json.dumps(config)
            org.save()
        elif not config.get('show_spoof_data'):
            config['show_spoof_data'] = False
            org.config = json.dumps(config)
            org.save()

class Migration(migrations.Migration):
    dependencies = [
        ('orgs_ext', '0002_auto_20150724_1609'),
    ]

    operations = [
        migrations.RunPython(add_show_spoof_data, migrations.RunPython.noop),
    ]
