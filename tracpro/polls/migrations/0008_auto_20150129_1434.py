# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0007_auto_20150129_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='is_complete',
            field=models.BooleanField(default=None, help_text='Whether this response is complete'),
            preserve_default=True,
        ),
    ]
