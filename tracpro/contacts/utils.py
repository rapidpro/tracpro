from __future__ import unicode_literals

import six

from celery.utils.log import get_task_logger

from temba_client.clients import TembaBadRequestError

from tracpro.client import get_client
from tracpro.utils import get_uuids


logger = get_task_logger(__name__)


def sync_pull_contacts(org, region_uuids, group_uuids):
    """
    Pull contacts from RapidPro and sync with local contacts.

    :param org: the org
    :param group_uuidss: the contact group UUIDs used - used to determine if local contact differs
    :return: tuple containing list of UUIDs for created, updated, deleted and failed contacts,
     and error/warning messages
    """
    from tracpro.contacts.models import Contact, NoMatchingCohortsWarning, NoUsableURNWarning

    # get all remote contacts for the specified groups
    client = get_client(org)
    incoming_contacts = client.get_contacts_in_groups(group_uuids | region_uuids)

    # get all existing local contacts (active or not) and organize by their UUID
    existing_contacts = Contact.objects.filter(org=org)
    existing_by_uuid = {contact.uuid: contact for contact in existing_contacts}

    created_uuids = []
    updated_uuids = []
    deleted_uuids = []
    failed_uuids = []
    errors = []

    total_contacts = 0
    for temba_contact in incoming_contacts:
        total_contacts += 1
        if not temba_contact.urns:
            msg = "%d Skipping contact: %s" % (total_contacts, temba_contact.name)
            logger.info(msg)
            # Just skip contacts without URNs
            continue

        elif temba_contact.uuid in created_uuids \
                or temba_contact.uuid in updated_uuids \
                or temba_contact.uuid in deleted_uuids \
                or temba_contact.uuid in failed_uuids:

            msg = "%d Skipping duplicate contact: %s" % (total_contacts, temba_contact.name)
            logger.info(msg)
            continue

        elif temba_contact.blocked:
            msg = "%d Deleting BLOCKED contact: %s" % (
                total_contacts, temba_contact.name)
            logger.info(msg)
            deleted_uuids.append(temba_contact.uuid)

        elif temba_contact.uuid in existing_by_uuid:

            msg = "%d Updating existing contact: %s" % (total_contacts, temba_contact.name)
            logger.info(msg)

            existing = existing_by_uuid[temba_contact.uuid]
            try:
                kwargs = Contact.kwargs_from_temba(org, temba_contact)
            except NoMatchingCohortsWarning as e:
                logger.warning(e.message)
                # This isn't really an error, we purposely only sync contacts in
                # the selected groups.
                failed_uuids.append(temba_contact.uuid)
                errors.append(e.message)
                # We know none of this contact's cohorts are selected, so mark it inactive.
                if existing.is_active:
                    existing.is_active = False
                    existing.save()
                continue
            except NoUsableURNWarning as e:
                # This is an error.  Their URN(s) don't have any of
                # the schemes that we support.
                logger.warning(e.message)
                failed_uuids.append(temba_contact.uuid)
                # Not a valid contact (for us, anyway).
                if existing.is_active:
                    existing.is_active = False
                    existing.save()
                continue

            for field, value in six.iteritems(kwargs):
                setattr(existing, field, value)

            existing.is_active = True
            existing.save()

            updated_uuids.append(temba_contact.uuid)
        else:
            # New contact (to us, anyway)
            try:
                kwargs = Contact.kwargs_from_temba(org, temba_contact)
            except NoMatchingCohortsWarning as e:
                # This isn't really an error, we purposely only sync contacts in
                # the selected groups.
                logger.warning(e.message)
                failed_uuids.append(temba_contact.uuid)
                errors.append(e.message)
                continue

            msg = "%d Adding NEW contact: %s" % (total_contacts, temba_contact.name)
            logger.info(msg)

            new_contact = Contact.objects.create(**kwargs)
            created_uuids.append(temba_contact.uuid)
            existing_by_uuid[new_contact.uuid] = new_contact

    # any contact that has been deleted from rapidpro
    # should be marked inactive in tracpro
    deleted_rapidpro_contacts = \
        client.get_contacts_in_groups(group_uuids | region_uuids, deleted=True)
    deleted_uuids += get_uuids(deleted_rapidpro_contacts)

    # Mark all deleted contacts as not active if they aren't already.
    existing_contacts.filter(uuid__in=deleted_uuids, is_active=True).update(is_active=False)

    return (list(set(created_uuids)),
            list(set(updated_uuids)),
            list(set(deleted_uuids)),
            list(set(failed_uuids)),
            errors)


def temba_compare_contacts(first, second):
    """
    Compares two Temba contacts to determine if there are differences.
    These two contacts are presumably referencing the same contact,
    but we need to see if there are any differences between them.

    Returns name of first difference found, one of 'name' or 'urns' or
    'groups' or 'fields', or None if no differences were spotted.
    """
    if first.uuid != second.uuid:  # pragma: no cover
        raise ValueError("Can't compare contacts with different UUIDs")

    if first.name != second.name:
        return 'name'

    if sorted(first.urns) != sorted(second.urns):
        return 'urns'

    if sorted(first.groups) != sorted(second.groups):
        return 'groups'

    if first.fields != second.fields:
        return 'fields'

    return None


def sync_push_contact(org, contact, change_type):
    """
    Pushes a local change to a contact.  Contact class must define
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
        remote_contacts = client.get_contacts(uuid=contact.uuid)
        if not remote_contacts:
            # No such contact at RapidPro, treat it like creating a contact.
            # (maybe somebody created then edited a contact before it got pushed to rapidpro?)
            sync_push_contact(org, contact, ChangeType.created)
            return
        remote_contact = remote_contacts[0]
        local_contact = contact.as_temba()

        if temba_compare_contacts(remote_contact, local_contact):
            # Something changed - make an update on rapidpro

            # fetched contacts may have fields with null values but we can't
            # push these so we remove them
            local_contact.fields = {
                k: v
                for k, v in six.iteritems(local_contact.fields)
                if v is not None
            }

            try:
                client.update_contact(contact=local_contact.uuid,
                                      name=local_contact.name,
                                      language=local_contact.language,
                                      urns=local_contact.urns,
                                      fields=local_contact.fields,
                                      groups=local_contact.groups)
            except TembaBadRequestError as e:
                temba_err_msg = ''
                for key, value in e.errors.iteritems():
                    temba_err_msg += key + ': ' + value[0]
                logger.warning("Unable to update contact %s on RapidPro. Error: %s" %
                               (local_contact.name, temba_err_msg))

    elif change_type == ChangeType.deleted:
        try:
            client.delete_contact(contact.uuid)
        except TembaBadRequestError as e:
            temba_err_msg = ''
            for key, value in e.errors.iteritems():
                temba_err_msg += key + ': ' + value[0]
            logger.warning("Unable to delete contact %s on RapidPro. Error: %s" % (contact.name, temba_err_msg))
