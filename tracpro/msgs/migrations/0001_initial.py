# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('orgs', '0008_org_timezone'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0004_auto_20150123_0909'),
        ('polls', '0014_remove_response_is_complete'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=640)),
                ('sent_on', models.DateTimeField(help_text='When the message was sent', auto_now_add=True)),
                ('cohort', models.CharField(max_length=1, verbose_name='Cohort', choices=[('A', 'All'), ('R', 'Respondents'), ('N', 'Non-respondents')])),
                ('status', models.CharField(help_text='Current status of this message', max_length=1, verbose_name='Status', choices=[('P', 'Pending'), ('S', 'Sent'), ('F', 'Failed')])),
                ('issue', models.ForeignKey(related_name='messages', verbose_name='Poll Issue', to='polls.Issue')),
                ('org', models.ForeignKey(related_name='messages', verbose_name='Organization', to='orgs.Org')),
                ('recipients', models.ManyToManyField(help_text='Contacts to whom this message was sent', related_name='messages', to='contacts.Contact')),
                ('region', models.ForeignKey(to='groups.Region')),
                ('sent_by', models.ForeignKey(related_name='messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
