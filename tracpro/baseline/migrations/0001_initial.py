# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0022_auto_20150716_1722'),
        ('orgs', '0014_auto_20150722_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaselineTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('baseline_poll', models.ForeignKey(related_name='baseline_terms', to='polls.Poll')),
                ('baseline_question', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, related_name='baseline_terms', chained_model_field=b'poll', to='polls.Question', chained_field=b'baseline_poll')),
                ('follow_up_poll', models.ForeignKey(to='polls.Poll')),
                ('follow_up_question', smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', chained_field=b'follow_up_poll', auto_choose=True, to='polls.Question')),
                ('org', models.ForeignKey(related_name='baseline_terms', verbose_name='Organization', to='orgs.Org')),
            ],
        ),
    ]
