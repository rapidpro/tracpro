# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='uuid',
            field=models.CharField(unique=True, max_length=36),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='region',
            name='uuid',
            field=models.CharField(unique=True, max_length=36),
            preserve_default=True,
        ),
    ]
