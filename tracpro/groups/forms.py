from django import forms
from django.utils.translation import ugettext_lazy as _


class ContactGroupsForm(forms.Form):
    groups = forms.MultipleChoiceField(
        choices=(), label=_("Groups"),
        help_text=_("Contact groups to use."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')
        initial = kwargs.pop('initial')

        super(ContactGroupsForm, self).__init__(*args, **kwargs)

        choices = []
        for group in org.get_temba_client().get_groups():
            choices.append((group.uuid, "%s (%d)" % (group.name, group.size)))

        self.fields['groups'].choices = choices
        self.fields['groups'].initial = initial
