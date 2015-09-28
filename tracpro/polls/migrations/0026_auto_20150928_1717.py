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
            field=models.CharField(max_length=1, editable=False, choices=[('p', 'Propagated to sub-children'), ('s', 'Spoofed'), ('r', 'Single Region'), ('u', 'Universal')]),
        ),
    ]
