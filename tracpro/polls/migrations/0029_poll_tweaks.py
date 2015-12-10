# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0028_question_tweaks'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='rapidpro_name',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='poll',
            name='flow_uuid',
            field=models.CharField(max_length=36),
        ),
        migrations.AlterField(
            model_name='poll',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='Show on TracPro'),
        ),
        migrations.AlterField(
            model_name='poll',
            name='name',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AlterField(
            model_name='poll',
            name='org',
            field=models.ForeignKey(related_name='polls', to='orgs.Org'),
        ),
        migrations.AlterUniqueTogether(
            name='poll',
            unique_together=set([('org', 'flow_uuid')]),
        ),
    ]
