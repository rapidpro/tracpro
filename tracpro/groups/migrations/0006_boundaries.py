# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0014_auto_20150722_1419'),
        ('groups', '0005_auto_20150805_2050'),
    ]

    operations = [
        migrations.CreateModel(
            name='Boundary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rapidpro_uuid', models.CharField(max_length=15, verbose_name='RapidPro UUID')),
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('level', models.IntegerField(null=True, verbose_name='level', choices=[(0, 'Country'), (1, 'State'), (2, 'District')])),
                ('geometry', models.TextField(help_text='The GeoJSON geometry of this boundary.', verbose_name='geojson')),
                ('org', models.ForeignKey(verbose_name='org', to='orgs.Org')),
                ('parent', models.ForeignKey(related_name='children', verbose_name='parent', to='groups.Boundary', null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='boundary',
            unique_together=set([('org', 'rapidpro_uuid')]),
        ),
    ]
