# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0005_auto_20150924_1938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='y_axis_title',
            field=models.CharField(default=b'', help_text='The title for the y axis of the chart.', max_length=255, blank=True),
        ),
    ]
