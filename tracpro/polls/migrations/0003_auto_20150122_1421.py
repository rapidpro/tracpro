# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_poll_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='poll',
            name='org',
            field=models.ForeignKey(related_name='polls', verbose_name='Organization', to='orgs.Org'),
            preserve_default=True,
        ),
    ]
