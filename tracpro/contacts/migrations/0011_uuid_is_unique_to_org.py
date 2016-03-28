# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0010_auto_20151111_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='uuid',
            field=models.CharField(max_length=36),
        ),
        migrations.AlterUniqueTogether(
            name='contact',
            unique_together=set([('uuid', 'org')]),
        ),
    ]
