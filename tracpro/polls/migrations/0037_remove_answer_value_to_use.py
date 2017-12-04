# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0036_set_summed_values'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='answer',
            name='value_to_use',
        ),
    ]
