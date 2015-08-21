# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0022_auto_20150716_1722'),
        ('orgs', '0014_auto_20150722_1419'),
        ('groups', '0005_auto_20150805_2050'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaselineTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='For example: 2015 Term 3 Attendance for P3 Girls', max_length=255)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('baseline_poll', models.ForeignKey(related_name='baseline_terms', to='polls.Poll')),
                ('baseline_question', smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', related_name='baseline_terms', chained_field=b'baseline_poll', auto_choose=True, to='polls.Question', help_text='The most recent response per user will be used as the baseline.')),
                ('follow_up_poll', models.ForeignKey(to='polls.Poll')),
                ('follow_up_question', smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', chained_field=b'follow_up_poll', auto_choose=True, to='polls.Question', help_text='Responses over time to compare to the baseline.')),
                ('org', models.ForeignKey(related_name='baseline_terms', verbose_name='Organization', to='orgs.Org')),
                ('region', models.ForeignKey(related_name='baseline_terms', to='groups.Region')),
            ],
        ),
    ]
