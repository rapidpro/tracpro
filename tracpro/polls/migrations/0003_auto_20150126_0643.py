# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_auto_20150126_0639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='conducted_on',
            field=models.DateTimeField(help_text='When the poll was conducted'),
            preserve_default=True,
        ),
    ]
