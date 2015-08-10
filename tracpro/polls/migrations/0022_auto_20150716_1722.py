# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0003_remove_message_issue'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0004_auto_20150123_0909'),
        ('polls', '0021_question_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='PollRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('conducted_on', models.DateTimeField(help_text='When the poll was conducted')),
                ('created_by', models.ForeignKey(related_name='pollruns_created', to=settings.AUTH_USER_MODEL, null=True)),
                ('poll', models.ForeignKey(related_name='pollruns', to='polls.Poll')),
                ('region', models.ForeignKey(related_name='pollruns', to='groups.Region', help_text='Region where poll was conducted', null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='issue',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='issue',
            name='poll',
        ),
        migrations.RemoveField(
            model_name='issue',
            name='region',
        ),
        migrations.RemoveField(
            model_name='response',
            name='issue',
        ),
        migrations.AlterField(
            model_name='question',
            name='type',
            field=models.CharField(max_length=1, choices=[('O', 'Open Ended'), ('C', 'Multiple Choice'), ('N', 'Numeric'), ('M', 'Menu'), ('K', 'Keypad'), ('R', 'Recording')]),
        ),
        migrations.DeleteModel(
            name='Issue',
        ),
        migrations.AddField(
            model_name='response',
            name='pollrun',
            field=models.ForeignKey(related_name='responses', to='polls.PollRun', null=True),
        ),
    ]
