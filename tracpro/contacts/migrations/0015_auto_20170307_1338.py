# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0014_auto_20170210_1659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='group',
            field=models.ForeignKey(related_name='contacts', verbose_name='Cohort', to='groups.Group', help_text='Cohort to which this contact belongs.', null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(help_text='All cohorts to which this contact belongs.', related_name='all_contacts', verbose_name='Cohorts', to='groups.Group'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='region',
            field=models.ForeignKey(related_name='contacts', verbose_name='Panel', to='groups.Region', help_text='Panel of this contact.'),
        ),
    ]
