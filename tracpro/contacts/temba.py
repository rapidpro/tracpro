from __future__ import absolute_import, unicode_literals

import logging

from collections import defaultdict
from dash.utils import intersection
from dash.utils.temba import temba_compare_contacts

logger = logging.getLogger(__name__)


def temba_pull_contacts(org, primary_groups, contact_class):
    """
    Pulls contacts from RapidPro and syncs with local contacts. Contact class must define a classmethod called
    kwargs_from_temba which generates field kwargs from a fetched temba contact.
    """
    client = org.get_temba_client()

    # get all existing contacts and organize by their UUID
    existing_contacts = contact_class.objects.filter(org=org)
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    # get all remote contacts in our primary groups
    incoming_contacts = client.get_contacts(groups=primary_groups)

    # organize incoming contacts by the UUID of their primary group
    incoming_by_primary = defaultdict(list)
    incoming_uuids = set()
    for incoming_contact in incoming_contacts:
        # ignore contacts with no URN
        if not incoming_contact.urns:
            logger.warning("Ignoring contact %s with no URN" % incoming_contact.uuid)
            continue

        # which primary groups is this contact in?
        contact_primary_groups = intersection(incoming_contact.groups, primary_groups)

        if len(contact_primary_groups) != 1:
            logger.warning("Ignoring contact %s who is in multiple primary groups" % incoming_contact.uuid)
            continue

        incoming_by_primary[contact_primary_groups[0]].append(incoming_contact)
        incoming_uuids.add(incoming_contact.uuid)

    created_uuids = []
    updated_uuids = []
    deleted_uuids = []

    for primary_group in primary_groups:
        incoming_contacts = incoming_by_primary[primary_group]

        for incoming in incoming_contacts:
            if incoming.uuid in existing_by_uuid:
                existing = existing_by_uuid[incoming.uuid]

                if temba_compare_contacts(incoming, existing.as_temba()) or not existing.is_active:
                    kwargs = contact_class.kwargs_from_temba(org, incoming)
                    for field, value in kwargs.iteritems():
                        setattr(existing, field, value)

                    existing.is_active = True
                    existing.save()

                    updated_uuids.append(incoming.uuid)
            else:
                kwargs = contact_class.kwargs_from_temba(org, incoming)
                contact_class.objects.create(**kwargs)
                created_uuids.append(kwargs['uuid'])

    # any existing contact not in the incoming set, is now deleted if not already deleted
    for existing_uuid, existing in existing_by_uuid.iteritems():
        if existing_uuid not in incoming_uuids and existing.is_active:
            deleted_uuids.append(existing_uuid)

    existing_contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    return created_uuids, updated_uuids, deleted_uuids
