# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_auto_20150123_0909'),
        ('polls', '0010_remove_question_show_with_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='regions',
            field=models.ManyToManyField(help_text='Regions where poll was conducted', related_name='issues', to='groups.Region'),
            preserve_default=True,
        ),
    ]
