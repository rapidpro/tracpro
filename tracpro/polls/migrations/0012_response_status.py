# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_status(apps, schema_editor):
    Response = apps.get_model("polls", "Response")
    for response in Response.objects.all():
        response.status = 'C' if response.is_complete else 'E'
        response.save(update_fields=('status',))


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0011_issue_regions'),
    ]

    operations = [
        migrations.AddField(
            model_name='response',
            name='status',
            field=models.CharField(default='C', help_text='Current status of this response', max_length=1, verbose_name='Status', choices=[('E', 'Empty'), ('P', 'Partial'), ('C', 'Complete')]),
            preserve_default=False,
        ),
    ]
