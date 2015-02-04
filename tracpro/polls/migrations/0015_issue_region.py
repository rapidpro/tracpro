# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_auto_20150123_0909'),
        ('polls', '0014_remove_response_is_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='region',
            field=models.ForeignKey(related_name='issues_2', to='groups.Region', help_text='Region where poll was conducted', null=True),
            preserve_default=True,
        ),
    ]
