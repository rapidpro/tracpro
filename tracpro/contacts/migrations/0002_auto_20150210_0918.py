# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='group',
            field=models.ForeignKey(related_name='contacts', verbose_name='Reporter group', to='groups.Group', null=True),
            preserve_default=True,
        ),
    ]
