# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from temba_client.base import TembaAPIError
from dash.orgs.models import Org

from ..models import Contact


def no_op(apps, schema_editor):
    # Do nothing on reversal
    pass


def update_contact_temba_modified_on(apps, schema_editor):
    # Connect to Temba to pull down latest modified date
    # for all contacts for every org
    for org in Org.objects.filter(is_active=True):
        client = org.get_temba_client()
        try:
            incoming_contacts = client.get_contacts()
        except TembaAPIError as e:
            continue

        for temba_contact in incoming_contacts:
            local_contact = Contact.objects.filter(uuid=temba_contact.uuid).first()
            if local_contact:
                local_contact.temba_modified_on = temba_contact.modified_on
                local_contact.save()

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_contact_temba_modified_on'),
    ]

    operations = [
        migrations.RunPython(update_contact_temba_modified_on, no_op),
    ]