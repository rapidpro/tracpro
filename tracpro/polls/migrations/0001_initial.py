# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
        ('orgs', '0008_org_timezone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
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
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_start_id', models.IntegerField()),
                ('created_on', models.DateTimeField(help_text='When this poll was created')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_uuid', models.CharField(unique=True, max_length=36)),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is active')),
                ('org', models.ForeignKey(related_name='polls', verbose_name='Organization', to='orgs.Org')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ruleset_uuid', models.CharField(unique=True, max_length=36)),
                ('text', models.CharField(max_length=64)),
                ('show_with_contact', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is active')),
                ('poll', models.ForeignKey(related_name='questions', to='polls.Poll')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flow_run_id', models.IntegerField()),
                ('contact', models.ForeignKey(related_name='responses', to='contacts.Contact')),
                ('issue', models.ForeignKey(related_name='responses', to='polls.Issue')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='issue',
            name='poll',
            field=models.ForeignKey(related_name='starts', to='polls.Poll'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='polls.Question'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='response',
            field=models.ForeignKey(related_name='answers', to='polls.Response'),
            preserve_default=True,
        ),
    ]
