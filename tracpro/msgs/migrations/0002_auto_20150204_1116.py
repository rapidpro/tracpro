# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='cohort',
            field=models.CharField(max_length=1, verbose_name='Cohort', choices=[('A', 'All participants'), ('R', 'Respondents'), ('N', 'Non-respondents')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='region',
            field=models.ForeignKey(related_name='messages', to='groups.Region', null=True),
            preserve_default=True,
        ),
    ]
