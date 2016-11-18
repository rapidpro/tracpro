# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0012_contact_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='groups',
            field=models.ManyToManyField(help_text='All groups to which this contact belongs.', related_name='all_contacts', verbose_name='Groups', to='groups.Group'),
        ),
    ]
