# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_auto_20150126_0643'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='decimal_value',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='flow_step_uuid',
        ),
        migrations.AddField(
            model_name='response',
            name='created_on',
            field=models.DateTimeField(default=timezone.now(), help_text='When this response was created'),
            preserve_default=False,
        ),
    ]
