# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_region_to_regions(apps, schema_editor):
    PollRun = apps.get_model("polls", "PollRun")
    for run in PollRun.objects.exclude(region=None):
        run.regions.add(run.region)
        run.save()


class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0024_pollrun_regions'),
    ]
    operations = [
        migrations.RunPython(migrate_region_to_regions, migrations.RunPython.noop),
    ]
