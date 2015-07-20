# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0022_auto_20150716_1722'),
        ('msgs', '0003_remove_message_issue'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='pollrun',
            field=models.ForeignKey(related_name='messages', verbose_name='Poll Run', to='polls.PollRun', null=True),
        ),
    ]
