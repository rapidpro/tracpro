from __future__ import unicode_literals

import six
from collections import OrderedDict

from celery.utils.log import get_task_logger

from temba_client.clients import TembaBadRequestError
from temba_client.v2.types import Contact as TembaContact

from tracpro.client import get_client
from tracpro.utils import get_uuids


logger = get_task_logger(__name__)


def sync_pull_contacts(org, group_uuids):
    """
    Pull contacts from RapidPro and sync with local contacts.

    :param org: the org
    :param group_uuidss: the contact group UUIDs used - used to determine if local contact differs
    :return: tuple containing list of UUIDs for created, updated, deleted and failed contacts
    """
    from tracpro.contacts.models import Contact, NoMatchingCohortsWarning
    from tracpro.groups.models import Group

    # get all remote contacts for the specified groups
    client = get_client(org)
    incoming_contacts = client.get_contacts_in_groups(group_uuids)

    # get all existing local contacts (active or not) and organize by their UUID
    existing_contacts = Contact.objects.filter(org=org)
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    created_uuids = []
    updated_uuids = []
    deleted_uuids = []
    failed_uuids = []

    groups = Group.objects.filter(uuid__in=group_uuids)

    for temba_contact in incoming_contacts:
        if not temba_contact.urns:
            # Just skip contacts without URNs
            continue

        elif temba_contact.blocked:
            deleted_uuids.append(temba_contact.uuid)

        elif temba_contact.uuid in existing_by_uuid:
            existing = existing_by_uuid[temba_contact.uuid]

            diff = temba_compare_contacts(temba_contact, existing.as_temba(), fields=(), groups=groups)

            if diff or not existing.is_active:
                try:
                    kwargs = Contact.kwargs_from_temba(org, temba_contact)
                except NoMatchingCohortsWarning as e:
                    logger.warning(e.message)
                    failed_uuids.append(temba_contact.uuid)
                    continue

                for field, value in six.iteritems(kwargs):
                    setattr(existing, field, value)

                existing.is_active = True
                existing.save()

                updated_uuids.append(temba_contact.uuid)
        else:
            try:
                kwargs = Contact.kwargs_from_temba(org, temba_contact)
            except NoMatchingCohortsWarning as e:
                logger.warning(e.message)
                failed_uuids.append(temba_contact.uuid)
                continue

            # We have a signal that queries rapidpro and sets groups on new Contacts,
            # but we already know the groups so we can skip that. This bit will let
            # the signal handler know which groups to add without having to call Rapidpro.
            new_contact = Contact(**kwargs)
            new_contact.new_groups = Group.objects.filter(uuid__in=get_uuids(temba_contact.groups))
            new_contact.save()
            created_uuids.append(kwargs['uuid'])

    # any contact that has been deleted from rapidpro
    # should be marked inactive in tracpro
    deleted_rapidpro_contacts = client.get_contacts_in_groups(group_uuids, deleted=True)
    deleted_uuids += get_uuids(deleted_rapidpro_contacts)

    # Mark all deleted contacts as not active if they aren't already.
    existing_contacts.filter(uuid__in=deleted_uuids, is_active=True).update(is_active=False)

    return created_uuids, updated_uuids, deleted_uuids, failed_uuids


def temba_compare_contacts(first, second, fields=None, groups=None):
    """
    Compares two Temba contacts to determine if there are differences.
    These two contacts are presumably referencing the same contact,
    but we need to see if there are any differences between them.
    fields: if this is passed in, we should check that these specific
            fields exist on both contacts, and
            ignore all other non-matching fields from the contacts
    groups: if this is passed in, we can check that the two contacts
            belong to the same groups

    Returns name of first difference found, one of 'name' or 'urns' or
    'groups' or 'fields', or None if no differences were spotted.
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't compare contacts with different UUIDs")

    if first.name != second.name:
        return 'name'

    if sorted(first.urns) != sorted(second.urns):
        return 'urns'

    if groups is None and (sorted(first.groups) != sorted(second.groups)):
        return 'groups'
    if groups:
        a = sorted(intersection(first.groups, groups))
        b = sorted(intersection(second.groups, groups))
        if a != b:
            return 'groups'

    if fields is None and (first.fields != second.fields):
        return 'fields'
    if fields and (filter_dict(first.fields, fields) != filter_dict(second.fields, fields)):
        return 'fields'

    return None


def sync_push_contact(org, contact, change_type, mutex_group_sets):
    """
    Pushes a local change to a contact. mutex_group_sets is a list of UUID sets
    of groups whose membership is mutually exclusive. Contact class must define
    an as_temba instance method.
    """
    from tracpro.contacts.models import ChangeType
    client = get_client(org)

    if change_type == ChangeType.created:
        temba_contact = contact.as_temba()
        try:
            temba_contact = client.create_contact(name=temba_contact.name,
                                                  language=temba_contact.language,
                                                  urns=temba_contact.urns,
                                                  fields=temba_contact.fields,
                                                  groups=temba_contact.groups)
        except TembaBadRequestError as e:
            temba_err_msg = ''
            for key, value in e.errors.iteritems():
                temba_err_msg += key + ': ' + value[0]
            logger.warning("Unable to create contact %s on RapidPro. Error: %s" % (temba_contact.name, temba_err_msg))
            return

        # update our contact with the new UUID from RapidPro
        contact.uuid = temba_contact.uuid
        contact.save()

    elif change_type == ChangeType.updated:
        # fetch contact so that we can merge with its URNs, fields and groups
        remote_contact = client.get_contacts(uuid=contact.uuid)[0]
        local_contact = contact.as_temba()

        if temba_compare_contacts(remote_contact, local_contact):
            merged_contact = temba_merge_contacts(
                local_contact, remote_contact, mutex_group_sets)

            # fetched contacts may have fields with null values but we can't
            # push these so we remove them
            merged_contact.fields = {k: v
                                     for k, v in six.iteritems(merged_contact.fields)
                                     if v is not None}

            try:
                client.update_contact(contact=merged_contact.uuid,
                                      name=merged_contact.name,
                                      language=merged_contact.language,
                                      urns=merged_contact.urns,
                                      fields=merged_contact.fields,
                                      groups=merged_contact.groups)
            except TembaBadRequestError as e:
                temba_err_msg = ''
                for key, value in e.errors.iteritems():
                    temba_err_msg += key + ': ' + value[0]
                logger.warning("Unable to update contact %s on RapidPro. Error: %s" %
                               (merged_contact.name, temba_err_msg))

    elif change_type == ChangeType.deleted:
        try:
            client.delete_contact(contact.uuid)
        except TembaBadRequestError as e:
            temba_err_msg = ''
            for key, value in e.errors.iteritems():
                temba_err_msg += key + ': ' + value[0]
            logger.warning("Unable to delete contact %s on RapidPro. Error: %s" % (merged_contact.name, temba_err_msg))


def temba_merge_contacts(first, second, mutex_group_sets):
    """
    Merges two Temba contacts, with priority given to the first contact
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't merge contacts with different UUIDs")

    # URNs are merged by scheme
    first_urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in first.urns]}
    urns_by_scheme = {u[0]: u[1] for u in [urn.split(':', 1) for urn in second.urns]}
    urns_by_scheme.update(first_urns_by_scheme)
    merged_urns = ['%s:%s' % (scheme, path) for scheme, path in six.iteritems(urns_by_scheme)]

    # fields are simple key based merge
    merged_fields = second.fields.copy()
    merged_fields.update(first.fields)

    # first merge mutually exclusive group sets
    first_groups = list(first.groups)
    second_groups = list(second.groups)
    merged_mutex_groups = []
    for group_set in mutex_group_sets:
        from_first = intersection(first_groups, group_set)
        if from_first:
            merged_mutex_groups.append(from_first[0])
        else:
            from_second = intersection(second_groups, group_set)
            if from_second:
                merged_mutex_groups.append(from_second[0])

        for group in group_set:
            if group in first_groups:
                first_groups.remove(group)
            if group in second_groups:
                second_groups.remove(group)

    # then merge the remaining groups
    merged_groups = merged_mutex_groups + union(first_groups, second_groups)

    return TembaContact.create(uuid=first.uuid, name=first.name,
                               urns=merged_urns, fields=merged_fields, groups=merged_groups)


def intersection(*args):
    """
    Return the intersection of lists, using the first list to determine item order
    """
    if not args:
        return []

    # remove duplicates from first list whilst preserving order
    base = list(OrderedDict.fromkeys(args[0]))

    if len(args) == 1:
        return base
    else:
        others = set(args[1]).intersection(*args[2:])
        return [e for e in base if e in others]


def filter_dict(d, keys):
    """
    Creates a new dict from an existing dict that only has the given keys
    """
    return {k: v for k, v in six.iteritems(d) if k in keys}


def union(*args):
    """
    Return the union of lists, ordering by first seen in any list
    """
    if not args:
        return []

    base = args[0]
    for other in args[1:]:
        base.extend(other)

    return list(OrderedDict.fromkeys(base))  # remove duplicates whilst preserving order
