# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0009_show_facility_code_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafield',
            name='key',
            field=models.CharField(max_length=255, verbose_name='key'),
        ),
        migrations.AlterField(
            model_name='datafield',
            name='label',
            field=models.CharField(max_length=255, verbose_name='label', blank=True),
        ),
        migrations.AlterField(
            model_name='datafield',
            name='org',
            field=models.ForeignKey(verbose_name='org', to='orgs.Org'),
        ),
        migrations.AlterField(
            model_name='datafield',
            name='show_on_tracpro',
            field=models.BooleanField(default=False, verbose_name='show_on_tracpro'),
        ),
        migrations.AlterField(
            model_name='datafield',
            name='value_type',
            field=models.CharField(max_length=1, verbose_name='value type', choices=[('T', 'Text'), ('N', 'Numeric'), ('D', 'Datetime'), ('S', 'State'), ('I', 'District')]),
        ),
    ]
