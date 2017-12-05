# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0036_set_summed_values'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='value_to_use',
        ),
        migrations.AddField(
            model_name='answer',
            name='last_value',
            field=models.CharField(help_text='For numeric questions, last answer from same contact on same day for same question. Otherwise, same as value.', max_length=640, null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='sum_value',
            field=models.CharField(help_text='For numeric questions, sum of answers from same contact on same day for same question. Otherwise, same as value.', max_length=640, null=True),
        ),
    ]
