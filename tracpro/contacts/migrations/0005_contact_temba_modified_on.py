# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0004_auto_20150324_1024'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='temba_modified_on',
            field=models.DateTimeField(help_text='When this item was last modified in Temba', null=True),
        ),
    ]
