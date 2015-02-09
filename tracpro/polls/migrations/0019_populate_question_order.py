# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_question_order(apps, schema_editor):
    Poll = apps.get_model("polls", "Poll")
    for poll in Poll.objects.all():
        q_num = 1
        for question in poll.questions.order_by('pk'):
            question.order = q_num
            question.save(update_fields=('order',))
            q_num += 1


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0018_question_order'),
    ]

    operations = [
        migrations.RunPython(populate_question_order),
    ]
