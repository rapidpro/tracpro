from __future__ import unicode_literals

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


# LATEST URN schemes from RapidPro - Sept 2017
# WE only use the scheme value (this list) and the label (2nd item in each entry, next list)
EMAIL_SCHEME = 'mailto'
EXTERNAL_SCHEME = 'ext'
FACEBOOK_SCHEME = 'facebook'
JIOCHAT_SCHEME = 'jiochat'
LINE_SCHEME = 'line'
TEL_SCHEME = 'tel'
TELEGRAM_SCHEME = 'telegram'
TWILIO_SCHEME = 'twilio'
TWITTER_SCHEME = 'twitter'
TWITTERID_SCHEME = 'twitterid'
VIBER_SCHEME = 'viber'
FCM_SCHEME = 'fcm'

# Scheme, Label, Export/Import Header, Context Key
URN_SCHEME_CONFIG = ((TEL_SCHEME, _("Phone number"), 'phone', 'tel_e164'),
                     (FACEBOOK_SCHEME, _("Facebook identifier"), 'facebook', FACEBOOK_SCHEME),
                     (TWITTER_SCHEME, _("Twitter handle"), 'twitter', TWITTER_SCHEME),
                     (TWITTERID_SCHEME, _("Twitter ID"), 'twitterid', TWITTERID_SCHEME),
                     (VIBER_SCHEME, _("Viber identifier"), 'viber', VIBER_SCHEME),
                     (LINE_SCHEME, _("LINE identifier"), 'line', LINE_SCHEME),
                     (TELEGRAM_SCHEME, _("Telegram identifier"), 'telegram', TELEGRAM_SCHEME),
                     (EMAIL_SCHEME, _("Email address"), 'email', EMAIL_SCHEME),
                     (EXTERNAL_SCHEME, _("External identifier"), 'external', EXTERNAL_SCHEME),
                     (JIOCHAT_SCHEME, _("Jiochat identifier"), 'jiochat', JIOCHAT_SCHEME),
                     (FCM_SCHEME, _("Firebase Cloud Messaging identifier"), 'fcm', FCM_SCHEME))

URN_SCHEME_CHOICES = [
    (c[0], c[1])
    for c in URN_SCHEME_CONFIG
]

URN_SCHEME_LABELS = dict(URN_SCHEME_CHOICES)


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
            return TEL_SCHEME, ''

    def render(self, name, value, attrs=None):
        output = ['<div class="urn-widget">',
                  super(URNWidget, self).render(name, value, attrs),
                  '</div>']
        return mark_safe(''.join(output))


class URNField(forms.fields.MultiValueField):

    def __init__(self, *args, **kwargs):
        fields = (forms.ChoiceField(choices=URN_SCHEME_CHOICES),
                  forms.CharField(max_length=32))
        super(URNField, self).__init__(fields, *args, **kwargs)
        self.widget = URNWidget(scheme_choices=URN_SCHEME_CHOICES)

    def compress(self, values):
        return '%s:%s' % (values[0], values[1])
