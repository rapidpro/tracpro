# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0032_uuid_is_unique_to_pollrun'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollrun',
            name='pollrun_type',
            field=models.CharField(max_length=1, editable=False, choices=[('u', 'Universal'), ('s', 'Spoofed'), ('r', 'Single Panel'), ('p', 'Propagated to sub-children')]),
        ),
        migrations.AlterField(
            model_name='pollrun',
            name='region',
            field=models.ForeignKey(blank=True, to='groups.Region', help_text='Panel where the poll was conducted.', null=True),
        ),
    ]
