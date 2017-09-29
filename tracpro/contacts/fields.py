from __future__ import unicode_literals

import re

import phonenumbers
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

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


def validate_twitter_handle(handle):
    handle_regex = r'^[a-zA-Z0-9_]{1,15}$'
    if not re.match(handle_regex, handle):
        raise ValidationError(
            _("That is not a valid format Twitter handle.  A valid handle has only "
              "letters A-Z, numbers 0-9, and underscores (_), and has up to 15 "
              "characters."))


def validate_numeric_twitter_id(numeric_id):
    if not numeric_id.isdigit():  # True only if all chars are digits
        raise ValidationError(
            _("That is not a valid format Twitter ID.  A valid numeric ID has only "
              "numbers 0-9."))


def validate_twitter_id(twitter_id):
    if '#' in twitter_id:
        numeric_id, handle = twitter_id.split('#', 1)
        validate_twitter_handle(handle)
        validate_numeric_twitter_id(numeric_id)
    else:
        raise ValidationError(
            _("That is not a valid format Twitter ID.  The correct format is: "
              "<numeric id>#<Twitter handle>"))


def validate_phone_used(number):
    from .models import Contact
    contacts = Contact.objects.all()
    phone_numbers = set()
    for contact in contacts:
        if contact.urn.startswith('tel'):
            phone_numbers.add(contact.urn.split(':')[1])

    if number in phone_numbers:
        raise ValidationError(
             _("This phone number is already being used by another contact."))


def validate_phone(number):
    try:
        parsed = phonenumbers.parse(number)
    except Exception as error:
        raise ValidationError(
            _(error._msg))
    else:
        reason = phonenumbers.is_possible_number_with_reason(parsed)
        if reason == 1:
            raise ValidationError(
                _("This phone number has an invalid country code."))
        elif reason == 2:
            raise ValidationError(
                _("This phone number is too short."))
        elif reason == 3:
            raise ValidationError(
                _("This phone number is too long."))
        else:
            validate_phone_used(number)


class URNField(forms.fields.MultiValueField):

    def __init__(self, *args, **kwargs):
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

    def clean(self, value):
        compressed_value = super(URNField, self).clean(value)
        scheme, address = compressed_value.split(':', 1)

        if scheme == URN_SCHEME_TWITTER:
            validate_twitter_handle(address)
            return compressed_value

        elif scheme == URN_SCHEME_TWITTERID:
            validate_twitter_id(address)
            return compressed_value

        elif scheme == URN_SCHEME_TEL:
            validate_phone(address)
            return compressed_value
