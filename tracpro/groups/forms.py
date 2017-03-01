from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.client import get_client


class ContactGroupsForm(forms.Form):
    groups = forms.MultipleChoiceField(
        choices=(), label=_("Groups"),
        help_text=_("Contact groups to use."),
        widget=forms.widgets.SelectMultiple(attrs={'size': '20'}),
    )

    def __init__(self, model, org, *args, **kwargs):
        self.model = model
        self.org = org

        super(ContactGroupsForm, self).__init__(*args, **kwargs)

        # Retrieve Contact Group choices from RapidPro.
        choices = [(group.uuid, "%s (%d)" % (group.name, group.count))
                   for group in get_client(org).get_groups()]
        # Sort choices by the labels, case-insensitively
        choices.sort(key=lambda item: item[1].lower())

        self.fields['groups'].choices = choices

        # Set initial group values from the org.
        initial = [r.uuid for r in self.model.get_all(self.org)]
        self.fields['groups'].initial = initial
