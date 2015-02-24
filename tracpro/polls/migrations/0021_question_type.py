# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0020_issue_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.CharField(default='C', max_length=1, choices=[('O', 'Open Ended'), ('C', 'Multiple Choice'), ('N', 'Numeric')]),
            preserve_default=False,
        ),
    ]
