# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0025_auto_20150907_1829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollrun',
            name='pollrun_type',
            field=models.CharField(max_length=1, editable=False, choices=[('u', 'Universal'), ('s', 'Spoofed'), ('r', 'Single Region'), ('p', 'Propagated to sub-children')]),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(max_length=1, choices=[('O', 'Open Ended'), ('C', 'Multiple Choice'), ('N', 'Numeric'), ('M', 'Menu'), ('K', 'Keypad'), ('R', 'Recording')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='status',
            field=models.CharField(help_text='Current status of this response', max_length=1, verbose_name='Status', choices=[('E', 'Empty'), ('P', 'Partial'), ('C', 'Complete')]),
        ),
    ]
