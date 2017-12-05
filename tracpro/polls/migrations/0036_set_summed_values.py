# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0035_auto_20170915_1615'),
        ('orgs', '0017_auto_20161026_1513'),
    ]

    operations = [
        migrations.RunPython(
            migrations.RunPython.noop,  # Not needed anymore, but the migration once existed so we're stuck with it
            migrations.RunPython.noop
        )
    ]
