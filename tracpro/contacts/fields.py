from __future__ import unicode_literals

from django import forms
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


class URNField(forms.fields.MultiValueField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'help_text',
            _('Format of Twitter handle is just the handle without the "@" at the front. '
              'Format of Twitter ID is <numeric id>#<Twitter handle> (again, no "@"). '
              'Format of phone number must include "+" and country code '
              '(e.g. "+1" for North America).'),
        )
        fields = (forms.ChoiceField(choices=URN_SCHEME_CHOICES),
                  forms.CharField(max_length=32))
        super(URNField, self).__init__(fields, *args, **kwargs)
        self.widget = URNWidget(scheme_choices=URN_SCHEME_CHOICES)

    def compress(self, values):
        return '%s:%s' % (values[0], values[1])
