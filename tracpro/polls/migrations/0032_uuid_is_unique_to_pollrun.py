# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0031_question_json_rules'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='flow_run_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterUniqueTogether(
            name='response',
            unique_together=set([('flow_run_id', 'pollrun')]),
        ),
    ]
