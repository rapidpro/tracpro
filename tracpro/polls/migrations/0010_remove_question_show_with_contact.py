# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0009_auto_20150130_0838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='show_with_contact',
        ),
    ]
