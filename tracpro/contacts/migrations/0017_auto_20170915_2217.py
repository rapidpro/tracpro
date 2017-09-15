# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0016_auto_20170913_1328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='group',
        ),
        migrations.AlterField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(help_text='All cohorts to which this contact belongs.', related_name='contacts', verbose_name='Cohorts', to='groups.Group'),
        ),
    ]
