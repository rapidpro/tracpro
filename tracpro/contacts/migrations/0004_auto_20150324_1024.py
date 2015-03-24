# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_auto_20150224_1245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='facility_code',
            field=models.CharField(help_text='Facility code for this contact', max_length=160, null=True, verbose_name='Facility Code', blank=True),
            preserve_default=True,
        ),
    ]
