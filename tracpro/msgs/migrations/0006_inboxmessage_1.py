# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0005_inboxmessage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='inboxmessage',
            old_name='contact_from',
            new_name='contact',
        ),
        migrations.AddField(
            model_name='inboxmessage',
            name='direction',
            field=models.CharField(max_length=1, null=True),
        ),
    ]
