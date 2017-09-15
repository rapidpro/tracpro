# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def forward(apps, schema_editor):
    Contact = apps.get_model("contacts", "Contact")
    for contact in Contact.objects.all():
        if contact.group:
            contact.groups.add(contact.group)

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0015_auto_20170307_1338'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
