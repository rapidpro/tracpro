# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0006_inboxmessage_1'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='region',
            field=models.ForeignKey(related_name='messages', verbose_name='panel', to='groups.Region', null=True),
        ),
    ]
