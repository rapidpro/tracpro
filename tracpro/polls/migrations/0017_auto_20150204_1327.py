# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0016_auto_20150204_1327'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='regions',
        ),
        migrations.AlterField(
            model_name='issue',
            name='region',
            field=models.ForeignKey(related_name='issues', to='groups.Region', help_text='Region where poll was conducted', null=True),
            preserve_default=True,
        ),
    ]
