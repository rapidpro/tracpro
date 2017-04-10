# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0008_uuid_is_unique_to_org'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'verbose_name': 'cohort'},
        ),
        migrations.AlterModelOptions(
            name='region',
            options={'verbose_name': 'panel'},
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.CharField(help_text='The name of this panel', max_length=128, verbose_name='Name', blank=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='name',
            field=models.CharField(help_text='The name of this panel', max_length=128, verbose_name='Name', blank=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='users',
            field=models.ManyToManyField(help_text='Users who can access this panel', related_name='regions', verbose_name='Users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together=set([]),
        ),
    ]
