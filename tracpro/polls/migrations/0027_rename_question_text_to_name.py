# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0026_auto_20150930_1334'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='text',
            new_name='name',
        )
    ]
