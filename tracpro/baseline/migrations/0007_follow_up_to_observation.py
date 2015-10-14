# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('baseline', '0006_auto_20150928_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineterm',
            name='follow_up_poll',
            field=models.ForeignKey(related_name='+', verbose_name='Observation Poll', to='polls.Poll'),
        ),
        migrations.AlterField(
            model_name='baselineterm',
            name='follow_up_question',
            field=smart_selects.db_fields.ChainedForeignKey(chained_model_field=b'poll', related_name='+', chained_field=b'follow_up_poll', verbose_name='Observation Question', auto_choose=True, to='polls.Question', help_text='Follow up poll responses over time to compare to the baseline values.'),
        ),
    ]
