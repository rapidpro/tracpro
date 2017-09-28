# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def forward(apps, schema_editor):
    ''' Copies any existing group this contact may have into groups'''
    Contact = apps.get_model("contacts", "Contact")
    for contact in Contact.objects.exclude(group=None):
        contact.groups.add(contact.group)

def backward(apps, schema_editor):
    ''' Takes the first group of contact's several groups
        and adds to the newly reproduced field 'group'.
        For development purposes, this seems resonable. '''
    Contact = apps.get_model("contacts", "Contact")
    for contact in Contact.objects.all():
        first_group = contact.groups.first()
        if first_group:
            contact.group = first_group
            contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0015_auto_20170307_1338'),
    ]

    operations = [
        migrations.RunPython(forward, backward)
    ]
