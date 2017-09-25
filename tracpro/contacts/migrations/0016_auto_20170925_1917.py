# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0015_auto_20170307_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='urn',
            field=models.CharField(help_text='How to communicate with this contact.', max_length=255, verbose_name='Phone/Twitter etc.'),
        ),
    ]
