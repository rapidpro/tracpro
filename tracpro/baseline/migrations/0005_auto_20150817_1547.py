# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0004_baselineterm_region'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='baseline_question',
            field=smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', related_name='baseline_terms', chained_field=b'baseline_poll', auto_choose=True, to='polls.Question', help_text='The most recent response per user will be used as the baseline.'),
        ),
        migrations.AlterField(
            model_name='baselineterm',
            name='follow_up_question',
            field=smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', chained_field=b'follow_up_poll', auto_choose=True, to='polls.Question', help_text='Responses over time to compare to the baseline.'),
        ),
    ]
