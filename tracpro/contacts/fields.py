from __future__ import unicode_literals

import re

from phonenumbers import NumberParseException, ValidationResult, parse, is_possible_number_with_reason

from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from tracpro.client import get_client

URN_SCHEME_TEL = 'tel'
URN_SCHEME_TWITTER = 'twitter'
URN_SCHEME_TWITTERID = 'twitterid'
URN_SCHEME_CHOICES = (
    (URN_SCHEME_TEL, _("Phone")),
    (URN_SCHEME_TWITTER, _("Twitter handle")),
    (URN_SCHEME_TWITTERID, _("Twitter ID")),
)

URN_SCHEME_LABELS = {
    scheme: label
    for scheme, label in URN_SCHEME_CHOICES
}

PHONE_PARSE_ERROR = {
    NumberParseException.INVALID_COUNTRY_CODE: "This phone number has an invalid country code.",
    NumberParseException.NOT_A_NUMBER: "This is not a valid phone number.  A valid phone number "
    "must include \"+\" and country code / region "
    "(e.g. \"+1\" for North America).",
    NumberParseException.TOO_SHORT_AFTER_IDD: "The string supplied is too short to be a phone number.",
    NumberParseException.TOO_SHORT_NSN: "The string supplied is too short to be a phone number.",
    NumberParseException.TOO_LONG: "The string supplied is too long to be a phone number.",
}


class URNWidget(forms.widgets.MultiWidget):

    def __init__(self, *args, **kwargs):
        scheme_choices = kwargs.pop('scheme_choices')
        widgets = (forms.Select(choices=scheme_choices),
                   forms.TextInput(attrs={'maxlength': 32}))
        super(URNWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split(':', 1)
        else:
            return URN_SCHEME_TEL, ''

    def render(self, name, value, attrs=None):
        output = ['<div class="urn-widget">',
                  super(URNWidget, self).render(name, value, attrs),
                  '</div>']
        return mark_safe(''.join(output))


def urn_exists_in_rapidpro(client, uuid, urn):
    """
    Return True if a remote contact with this urn
    exists in RapidPro and has a different uuid than uuid.
    """
    contacts = client.get_contacts(urn=urn)
    try:
        return contacts[0].uuid is not None and contacts[0].uuid != uuid
    except:
        return False


def urn_already_used(client, uuid, urn):
    """Return True if a local or remote contact
        with this urn exists and has a different uuid than uuid"""

    from .models import Contact
    # RapidPro checks for the numeric id without handle
    # we are going to mimic that here locally
    if urn.startswith('twitterid'):
        contacts = Contact.objects.filter(urn__startswith=urn.split('#')[0])
        if uuid:
            contacts = contacts.exclude(uuid=uuid)
    else:
        contacts = Contact.objects.filter(urn=urn)
        if uuid:
            contacts = contacts.exclude(uuid=uuid)

    return contacts.exists() or urn_exists_in_rapidpro(client, uuid, urn)


def validate_twitter_handle(client, uuid, handle, from_id=False):
    handle_regex = r'^[a-zA-Z0-9_]{1,15}$'
    if not re.match(handle_regex, handle):
        raise ValidationError(
            _("This is not a valid Twitter handle.  A valid handle has only "
              "letters A-Z, numbers 0-9, and underscores (_), and has up to 15 "
              "characters."))
    elif not from_id and urn_already_used(client, uuid, 'twitter:%s' % handle):
        raise ValidationError(
            _("This Twitter Handle is already being used by another contact."))


def validate_numeric_twitter_id(numeric_id):
    if not numeric_id.isdigit():  # True only if all chars are digits
        raise ValidationError(
            _("This is not a valid numeric ID.  A valid numeric ID has only "
              "numbers 0-9."))


def validate_twitter_id(client, uuid, twitter_id):
    if '#' in twitter_id:
        numeric_id, handle = twitter_id.split('#', 1)
        validate_twitter_handle(client, uuid, handle, True)
        validate_numeric_twitter_id(numeric_id)
        if urn_already_used(client, uuid, 'twitterid:%s' % twitter_id):
            raise ValidationError(
                _("This Twitter ID is already being used by another contact."))
    else:
        raise ValidationError(
            _("This is not a valid numeric ID.  The correct format is: "
              "<numeric id>#<Twitter handle>"))


def validate_phone_used(client, uuid, parsed):
    phone_number = '%s%s%s' % ('+', parsed.country_code, parsed.national_number)
    urn = 'tel:%s' % phone_number

    if urn_already_used(client, uuid, urn):
        raise ValidationError(
             _("This phone number is already being used by another contact."))
    else:
        return urn


def validate_phone(client, uuid, number):
    try:
        parsed = parse(number)
    except NumberParseException as error:
        raise ValidationError(
            _(PHONE_PARSE_ERROR[error.error_type]))
    else:
        reason = is_possible_number_with_reason(parsed)
        if reason == ValidationResult.INVALID_COUNTRY_CODE:
            raise ValidationError(
                _(PHONE_PARSE_ERROR[NumberParseException.INVALID_COUNTRY_CODE]))
        elif reason == ValidationResult.TOO_SHORT:
            raise ValidationError(
                _(PHONE_PARSE_ERROR[NumberParseException.TOO_SHORT_NSN]))
        elif reason == ValidationResult.TOO_LONG:
            raise ValidationError(
                _(PHONE_PARSE_ERROR[NumberParseException.TOO_LONG]))
        else:
            return validate_phone_used(client, uuid, parsed)


class URNField(forms.fields.MultiValueField):

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop('org', None)
        self.uuid = kwargs.pop('uuid', None)
        kwargs.setdefault(
            'help_text',
            _('Format of Twitter handle is just the handle without the "@" at the front. '
              'Format of Twitter ID is <numeric id>#<Twitter handle> (again, no "@"). '
              'Format of phone number must include "+" and country code / region '
              '(e.g. "+1" for North America).'),
        )
        fields = (forms.ChoiceField(choices=URN_SCHEME_CHOICES),
                  forms.CharField(max_length=32))
        super(URNField, self).__init__(fields, *args, **kwargs)
        self.widget = URNWidget(scheme_choices=URN_SCHEME_CHOICES)

    def compress(self, values):
        return '%s:%s' % (values[0], values[1])

    def clean(self, value, *args, **kwargs):
        compressed_value = super(URNField, self).clean(value)
        scheme, address = compressed_value.split(':', 1)

        client = get_client(self.org)

        if scheme == URN_SCHEME_TWITTER:
            validate_twitter_handle(client, self.uuid, address)
            return compressed_value

        elif scheme == URN_SCHEME_TWITTERID:
            validate_twitter_id(client, self.uuid, address)
            return compressed_value

        elif scheme == URN_SCHEME_TEL:
            urn = validate_phone(client, self.uuid, address)
            return urn

        else:
            raise ValidationError(
                _('URN does not appear to match any that we understand'))
