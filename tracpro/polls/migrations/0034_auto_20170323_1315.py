# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0033_auto_20170307_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollrun',
            name='region',
            field=models.ForeignKey(blank=True, to='groups.Region', help_text='Panel where the poll was conducted.', null=True, verbose_name='panel'),
        ),
    ]
