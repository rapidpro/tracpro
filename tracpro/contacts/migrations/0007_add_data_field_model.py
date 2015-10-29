# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0014_auto_20150722_1419'),
        ('contacts', '0006_contact_help_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255, blank=True)),
                ('key', models.CharField(max_length=255)),
                ('value_type', models.CharField(max_length=1, choices=[('T', 'Text'), ('N', 'Numeric'), ('D', 'Datetime'), ('S', 'State'), ('I', 'District')])),
                ('show_on_tracpro', models.BooleanField(default=False)),
                ('org', models.ForeignKey(to='orgs.Org')),
            ],
            options={'ordering': ('label', 'key')},
        ),
        migrations.AlterUniqueTogether(
            name='datafield',
            unique_together=set([('org', 'key')]),
        ),
    ]
