# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('orgs', '0009_auto_20150121_1449'),
    ]

    operations = [
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_uuid', models.CharField(max_length=36)),
                ('name', models.CharField(max_length=64, verbose_name='Name of this poll')),
                ('org', models.ForeignKey(related_name='polls', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_step_uuid', models.CharField(max_length=36)),
                ('category', models.CharField(max_length=36, null=True)),
                ('value', models.CharField(max_length=640, null=True)),
                ('decimal_value', models.DecimalField(null=True, max_digits=36, decimal_places=8)),
                ('submitted_on', models.DateTimeField(help_text='When this answer was submitted')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_start_uuid', models.CharField(max_length=36)),
                ('created_on', models.DateTimeField(help_text='When this poll was created')),
                ('poll', models.ForeignKey(related_name='starts', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rule_set_uuid', models.CharField(max_length=36)),
                ('name', models.CharField(max_length=64)),
                ('show_with_contact', models.BooleanField(default=False)),
                ('poll', models.ForeignKey(related_name='questions', to='polls.Poll')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_run_uuid', models.CharField(max_length=36)),
                ('contact', models.ForeignKey(related_name='responses', to='contacts.Contact')),
                ('issue', models.ForeignKey(related_name='responses', to='polls.PollIssue')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='pollanswer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='polls.PollQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pollanswer',
            name='response',
            field=models.ForeignKey(related_name='answers', to='polls.PollResponse'),
            preserve_default=True,
        ),
    ]
