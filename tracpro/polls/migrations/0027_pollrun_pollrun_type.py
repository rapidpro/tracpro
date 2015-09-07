# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0026_remove_pollrun_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='pollrun',
            name='pollrun_type',
            field=models.CharField(default='', max_length=1, editable=False, choices=[('p', 'Propagated to sub-children'), ('r', 'Single Region'), ('u', 'Universal')]),
            preserve_default=False,
        ),
    ]
