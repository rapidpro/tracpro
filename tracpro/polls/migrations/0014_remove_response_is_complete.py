# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0013_auto_20150203_0953'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='response',
            name='is_complete',
        ),
    ]
