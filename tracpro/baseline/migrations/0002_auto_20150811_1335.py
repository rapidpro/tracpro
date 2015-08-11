# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='name',
            field=models.CharField(help_text='For example: 2015 Term 3 Attendance for P3 Girls', max_length=255),
        ),
    ]
