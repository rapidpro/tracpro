# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0009_auto_20150121_1449'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36)),
                ('name', models.CharField(help_text='The name of this region', max_length=128, verbose_name='Name', blank=True)),
                ('org', models.ForeignKey(related_name='groups', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(max_length=36)),
                ('name', models.CharField(help_text='The name of this region', max_length=128, verbose_name='Name', blank=True)),
                ('org', models.ForeignKey(related_name='regions', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
