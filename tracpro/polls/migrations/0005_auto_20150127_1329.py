# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_auto_20150126_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='flow_start_id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
