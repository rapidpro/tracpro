# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this item is active'),
            preserve_default=True,
        ),
    ]
