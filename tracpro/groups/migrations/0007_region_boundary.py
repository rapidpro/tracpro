# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0006_boundaries'),
    ]

    operations = [
        migrations.AddField(
            model_name='region',
            name='boundary',
            field=models.ForeignKey(related_name='regions', on_delete=django.db.models.deletion.SET_NULL, verbose_name='boundary', to='groups.Boundary', null=True),
        ),
    ]
