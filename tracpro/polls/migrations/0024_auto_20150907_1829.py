# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0023_auto_20150831_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='pollrun',
            name='pollrun_type',
            field=models.CharField(default='', max_length=1, editable=False, choices=[('p', 'Propagated to sub-children'), ('r', 'Single Region'), ('u', 'Universal')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pollrun',
            name='conducted_on',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='When the poll was conducted'),
        ),
        migrations.AlterField(
            model_name='pollrun',
            name='region',
            field=models.ForeignKey(blank=True, to='groups.Region', help_text='Region where the poll was conducted.', null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(max_length=1, choices=[('C', 'Multiple Choice'), ('K', 'Keypad'), ('M', 'Menu'), ('O', 'Open Ended'), ('N', 'Numeric'), ('R', 'Recording')]),
        ),
        migrations.AlterField(
            model_name='response',
            name='status',
            field=models.CharField(help_text='Current status of this response', max_length=1, verbose_name='Status', choices=[('P', 'Partial'), ('C', 'Complete'), ('E', 'Empty')]),
        ),
    ]
