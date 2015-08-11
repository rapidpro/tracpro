# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0002_auto_20150811_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='end_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='baselineterm',
            name='start_date',
            field=models.DateTimeField(),
        ),
    ]
