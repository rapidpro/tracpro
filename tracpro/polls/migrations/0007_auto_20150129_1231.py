# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0006_auto_20150129_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='is_complete',
            field=models.BooleanField(default=True, help_text='Whether this response is complete'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='response',
            name='updated_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 1, 29, 12, 31, 24, 36711, tzinfo=utc), help_text='When the last activity on this response was'),
            preserve_default=False,
        ),
    ]
