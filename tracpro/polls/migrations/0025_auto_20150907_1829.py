# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_pollrun_type(apps, schema_editor):
    PollRun = apps.get_model('polls', 'PollRun')
    for pollrun in PollRun.objects.all():
        if pollrun.region_id:
            pollrun.pollrun_type = 'r'  # regional
        else:
            pollrun.pollrun_type = 'u'  # universal
        pollrun.save()


class Migration(migrations.Migration):
    dependencies = [
        ('polls', '0024_auto_20150907_1829'),
    ]
    operations = [
        migrations.RunPython(set_pollrun_type, migrations.RunPython.noop),
    ]
