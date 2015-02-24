# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_auto_20150210_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='facility_code',
            field=models.CharField(help_text='Facility code for this contact', max_length=16, null=True, verbose_name='Facility Code', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contact',
            name='language',
            field=models.CharField(help_text='Language for this contact', max_length=3, null=True, verbose_name='Language', blank=True),
            preserve_default=True,
        ),
    ]
