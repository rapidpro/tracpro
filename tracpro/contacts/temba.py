from __future__ import absolute_import, unicode_literals

import logging

from collections import defaultdict
from dash.utils import intersection
from dash.utils.temba import temba_compare_contacts, temba_merge_contacts
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    created = 1
    updated = 2
    deleted = 3


def temba_sync_contact(org, contact, change_type, primary_groups):
    """
    Syncs a local change to a contact
    :param org: the org
    :param contact: the contact
    :param change_type: the change type
    :param primary_groups: a set of group UUIDs which represent the primary groups for this org. Membership of primary
    groups is mutually exclusive
    """
    client = org.get_temba_client()

    if change_type == ChangeType.created:
        temba_contact = contact.as_temba()
        temba_contact = client.create_contact(temba_contact.name,
                                              temba_contact.urns,
                                              temba_contact.fields,
                                              temba_contact.groups)
        # update our contact with the new UUID from RapidPro
        contact.uuid = temba_contact.uuid
        contact.save()

    elif change_type == ChangeType.updated:
        # fetch contact so that we can merge with its URNs, fields and groups
        remote_contact = client.get_contact(contact.uuid)
        local_contact = contact.as_temba()

        if temba_compare_contacts(remote_contact, local_contact):
            merged_contact = temba_merge_contacts(local_contact, remote_contact, primary_groups)

            client.update_contact(merged_contact.uuid,
                                  merged_contact.name,
                                  merged_contact.urns,
                                  merged_contact.fields,
                                  merged_contact.groups)

    elif change_type == ChangeType.deleted:
        client.delete_contact(contact.uuid)


def temba_pull_contacts(org, primary_groups, group_class, contact_class):
    """
    Pulls contacts from RapidPro and syncs with local contacts
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
        group_obj = group_class.objects.get(uuid=primary_group)

        for incoming in incoming_contacts:
            if incoming.uuid in existing_by_uuid:
                existing = existing_by_uuid[incoming.uuid]

                if temba_compare_contacts(incoming, existing.as_temba()) or not existing.is_active:
                    existing.update_from_temba(org, group_obj, incoming)
                    updated_uuids.append(incoming.uuid)
            else:
                created = contact_class.from_temba(org, group_obj, incoming)
                created_uuids.append(created.uuid)

    # any existing contact not in the incoming set, is now deleted if not already deleted
    for existing_uuid, existing in existing_by_uuid.iteritems():
        if existing_uuid not in incoming_uuids and existing.is_active:
            deleted_uuids.append(existing_uuid)

    existing_contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    return created_uuids, updated_uuids, deleted_uuids
