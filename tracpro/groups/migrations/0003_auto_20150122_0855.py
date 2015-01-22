# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0002_auto_20150122_0754'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this region is active'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='region',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this region is active'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='region',
            name='users',
            field=models.ManyToManyField(help_text='Users who can access this region', related_name='regions', verbose_name='Users', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
