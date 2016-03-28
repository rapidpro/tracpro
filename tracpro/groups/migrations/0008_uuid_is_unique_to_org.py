# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0007_region_boundary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='uuid',
            field=models.CharField(max_length=36),
        ),
        migrations.AlterField(
            model_name='region',
            name='uuid',
            field=models.CharField(max_length=36),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together=set([('org', 'uuid')]),
        ),
    ]
