from collections import OrderedDict

def sync_pull_contacts(org, contact_class, fields=None, groups=None,
                       last_time=None, delete_blocked=False):
    """
    Pulls updated contacts or all contacts from RapidPro and syncs with local contacts.
    Contact class must define a class method called kwargs_from_temba which generates
    field kwargs from a fetched temba contact.
    :param org: the org
    :param contact_class: the contact class type
    :param fields: the contact field keys used - used to determine if local contact differs
    :param groups: the contact group UUIDs used - used to determine if local contact differs
    :param last_time: the last time we pulled contacts, if None, sync all contacts
    :param delete_blocked: if True, delete the blocked contacts
    :return: tuple containing list of UUIDs for created, updated, deleted and failed contacts
    """
    # get all remote contacts
    client = org.get_temba_client(api_version=2)
    updated_incoming_contacts = []
    if last_time:
        updated_incoming_contacts = client.get_contacts(after=last_time).all()
    else:
        updated_incoming_contacts = client.get_contacts().all()

    # get all existing contacts and organize by their UUID
    existing_contacts = contact_class.objects.filter(org=org)
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    created_uuids = []
    updated_uuids = []
    deleted_uuids = []
    failed_uuids = []

    for updated_incoming in updated_incoming_contacts:
        # delete blocked contacts if deleted_blocked=True
        if updated_incoming.blocked and delete_blocked:
            deleted_uuids.append(updated_incoming.uuid)

        elif updated_incoming.uuid in existing_by_uuid:
            existing = existing_by_uuid[updated_incoming.uuid]

            diff = temba_compare_contacts(updated_incoming, existing.as_temba(), fields, groups)

            if diff or not existing.is_active:
                try:
                    kwargs = contact_class.kwargs_from_temba(org, updated_incoming)
                    import ipdb; ipdb.set_trace()
                except ValueError:
                    failed_uuids.append(updated_incoming.uuid)
                    continue

                for field, value in six.iteritems(kwargs):
                    setattr(existing, field, value)

                existing.is_active = True
                existing.save()

                updated_uuids.append(updated_incoming.uuid)
        else:
            try:
                kwargs = contact_class.kwargs_from_temba(org, updated_incoming)
            except ValueError:
                failed_uuids.append(updated_incoming.uuid)
                continue

            contact_class.objects.create(**kwargs)
            created_uuids.append(kwargs['uuid'])

    # any contact that has been deleted from rapidpro
    # should also be deleted from dash
    # if last_time was passed in, just get contacts deleted after the last time we synced
    if last_time:
        deleted_incoming_contacts = client.get_contacts(deleted=True, after=last_time).all()
    else:
        deleted_incoming_contacts = client.get_contacts(deleted=True).all()
    for deleted_incoming in deleted_incoming_contacts:
        deleted_uuids.append(deleted_incoming.uuid)
    existing_contacts.filter(uuid__in=deleted_uuids).update(is_active=False)

    return created_uuids, updated_uuids, deleted_uuids, failed_uuids

def temba_compare_contacts(first, second, fields=None, groups=None):
    """
    Compares two Temba contacts to determine if there are differences. Returns
    first difference found.
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