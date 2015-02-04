# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_region(apps, schema_editor):
    Issue = apps.get_model("polls", "Issue")
    for issue in Issue.objects.all():
        if issue.regions.count() == 1:
            issue.region = issue.regions.first()
            issue.save(update_fields=('region',))


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0015_issue_region'),
    ]

    operations = [
        migrations.RunPython(populate_region)
    ]
