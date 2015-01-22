# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0009_auto_20150121_1449'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0002_auto_20150122_0754'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=36)),
                ('name', models.CharField(help_text='The name of this contact', max_length=128, verbose_name='Name', blank=True)),
                ('urn', models.CharField(max_length=255, verbose_name='URN')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this contact is active')),
                ('created_on', models.DateTimeField(help_text='When this item was originally created', auto_now_add=True)),
                ('modified_on', models.DateTimeField(help_text='When this item was last modified', auto_now=True)),
                ('created_by', models.ForeignKey(related_name='contact_creations', to=settings.AUTH_USER_MODEL, help_text='The user which originally created this item', null=True)),
                ('group', models.ForeignKey(related_name='contacts', verbose_name='Reporter group', to='groups.Group')),
                ('modified_by', models.ForeignKey(related_name='contact_modifications', to=settings.AUTH_USER_MODEL, help_text='The user which last modified this item', null=True)),
                ('org', models.ForeignKey(related_name='contacts', verbose_name='Organization', to='orgs.Org')),
                ('region', models.ForeignKey(related_name='contacts', verbose_name='Region', to='groups.Region', help_text='Region or state this contact lives in')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
