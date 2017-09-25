# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0034_auto_20170323_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='value_to_use',
            field=models.CharField(help_text="For numeric questions for orgs that want to use the sum of numeric responses from the same contact on the same day, the sum of those responses. For all others, just a copy of 'value'.", max_length=640, null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='value',
            field=models.CharField(help_text='Value from rapidpro', max_length=640, null=True),
        ),
    ]
