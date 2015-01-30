# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0008_auto_20150129_1434'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='flow_start_id',
        ),
        migrations.AddField(
            model_name='response',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this response is active'),
            preserve_default=True,
        ),
    ]
