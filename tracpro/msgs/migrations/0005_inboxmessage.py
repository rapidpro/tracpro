# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0013_auto_20150715_1831'),
        ('contacts', '0004_auto_20150324_1024'),
        ('msgs', '0004_message_pollrun'),
    ]

    operations = [
        migrations.CreateModel(
            name='InboxMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rapidpro_message_id', models.IntegerField()),
                ('text', models.CharField(max_length=640, null=True)),
                ('archived', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(null=True)),
                ('delivered_on', models.DateTimeField(null=True)),
                ('sent_on', models.DateTimeField(null=True)),
                ('contact_from', models.ForeignKey(related_name='inbox_messages', to='contacts.Contact')),
                ('org', models.ForeignKey(related_name='inbox_messages', verbose_name='Organization', to='orgs.Org')),
            ],
        ),
    ]
