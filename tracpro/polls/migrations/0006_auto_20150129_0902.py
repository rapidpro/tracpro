# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0005_auto_20150127_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='flow_run_id',
            field=models.IntegerField(unique=True),
            preserve_default=True,
        ),
    ]
