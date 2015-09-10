# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0003_auto_20150910_1814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='end_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='baselineterm',
            name='start_date',
            field=models.DateField(),
        ),
    ]
