# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='issue',
            old_name='created_on',
            new_name='conducted_on',
        ),
        migrations.AlterField(
            model_name='issue',
            name='poll',
            field=models.ForeignKey(related_name='issues', to='polls.Poll'),
            preserve_default=True,
        ),
    ]
