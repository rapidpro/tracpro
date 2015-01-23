# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0003_auto_20150122_0855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this item is active'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='region',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this item is active'),
            preserve_default=True,
        ),
    ]
