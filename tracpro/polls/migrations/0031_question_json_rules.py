# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0030_reset_question_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='json_rules',
            field=models.TextField(verbose_name='RapidPro rules', blank=True),
        ),
    ]
