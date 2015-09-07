# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0025_auto_20150906_1412'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pollrun',
            name='region',
        ),
    ]
