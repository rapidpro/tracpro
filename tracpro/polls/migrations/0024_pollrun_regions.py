# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0005_auto_20150805_2050'),
        ('polls', '0023_auto_20150831_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='pollrun',
            name='regions',
            field=models.ManyToManyField(help_text='Regions where the poll was conducted.', to='groups.Region', blank=True),
        ),
    ]
