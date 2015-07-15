# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0021_question_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(max_length=1, choices=[('O', 'Open Ended'), ('C', 'Multiple Choice'), ('N', 'Numeric'), ('M', 'Menu'), ('K', 'Keypad'), ('R', 'Recording')]),
        ),
    ]
