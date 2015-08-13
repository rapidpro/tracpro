# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_auto_20150123_0909'),
        ('baseline', '0003_auto_20150811_1508'),
    ]

    operations = [
        migrations.AddField(
            model_name='baselineterm',
            name='region',
            field=models.ForeignKey(
                related_name='baseline_terms', default=1, to='groups.Region'),
            preserve_default=False,
        ),
    ]
