# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('polls', '0019_populate_question_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='created_by',
            field=models.ForeignKey(related_name='issues_created', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
