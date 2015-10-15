# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_contact_temba_modified_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='group',
            field=models.ForeignKey(related_name='contacts', verbose_name='Reporter group', to='groups.Group', help_text='Reporter group to which this contact belongs.', null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='name',
            field=models.CharField(help_text='The name of this contact', max_length=128, verbose_name='Full name', blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='region',
            field=models.ForeignKey(related_name='contacts', verbose_name='Region', to='groups.Region', help_text='Region where this contact lives.'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='urn',
            field=models.CharField(help_text='Phone number or Twitter handle of this contact.', max_length=255, verbose_name='Phone/Twitter'),
        ),
    ]
