# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0016_auto_20170913_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='group',
            field=models.ForeignKey(related_name='old_contacts', verbose_name='Cohort', to='groups.Group', help_text='Cohort to which this contact belongs.', null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(help_text='All cohorts to which this contact belongs.', related_name='contacts', verbose_name='Cohorts', to='groups.Group'),
        ),
    ]
