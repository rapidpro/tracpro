# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_uuid_is_unique_to_org'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafield',
            name='value_type',
            field=models.CharField(max_length=1, verbose_name='value type', choices=[('T', 'Text'), ('N', 'Numeric'), ('D', 'Datetime'), ('S', 'State'), ('I', 'District'), ('N', 'Numeric'), ('W', 'Ward')]),
        ),
    ]
