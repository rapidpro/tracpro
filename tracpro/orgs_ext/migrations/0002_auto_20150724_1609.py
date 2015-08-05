# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.conf import settings
from django.db import models, migrations


def add_available_languages(apps, schema_editor):
    """Set default available_languages to all languages defined for this project."""
    all_languages = [l[0] for l in settings.LANGUAGES]
    for org in apps.get_model('orgs', 'Org').objects.all():
        updated = False
        config = json.loads(org.config) if org.config else {}
        if not config.get('available_languages'):
            config['available_languages'] = all_languages
            org.config = json.dumps(config)
            updated = True
        if not org.default_language:
            org.default_language = settings.DEFAULT_LANGUAGE
            updated = True
        if updated:
            org.save()


class Migration(migrations.Migration):
    dependencies = [
        ('orgs_ext', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_available_languages, migrations.RunPython.noop),
    ]
