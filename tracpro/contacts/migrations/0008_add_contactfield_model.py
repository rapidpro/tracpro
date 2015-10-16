# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0007_add_data_field_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=255, null=True)),
                ('contact', models.ForeignKey(to='contacts.Contact')),
                ('field', models.ForeignKey(to='contacts.DataField')),
            ],
        ),
    ]
