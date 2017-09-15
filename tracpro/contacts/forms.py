from __future__ import absolute_import, unicode_literals

from django import forms
from django.db.models.functions import Lower
from django.utils.translation import ugettext_lazy as _

from tracpro.groups.models import Group, Region
from tracpro.groups.fields import ModifiedLevelTreeNodeChoiceField

from .fields import URNField
from . import models


class ContactForm(forms.ModelForm):
    urn = URNField(label=_("Phone/Twitter"))
    region = ModifiedLevelTreeNodeChoiceField(
        label=_("Panel"), empty_label="", queryset=Region.objects.none())

    class Meta:
        model = models.Contact
        fields = ['name', 'urn', 'region', 'groups', 'language']
        widgets = {
            'language': forms.TextInput(attrs={'class': 'language-field'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        org = self.user.get_org()
        super(ContactForm, self).__init__(*args, **kwargs)

        self.instance.org = org
        self.instance.modified_by = self.user
        if not self.instance.pk:
            self.instance.created_by = self.user

        self.fields['name'].required = True
        self.fields['groups'].required = True

        regions = self.user.get_all_regions(org).order_by(Lower('name'))
        self.fields['region'].queryset = regions
        self.fields['group'].empty_label = ""
        self.fields['group'].queryset = Group.get_all(org).order_by(Lower('name'))

        # Add form fields to update contact's DataField values.
        self.data_field_keys = []
        values = {v.field.key: v.get_value() for v in self.instance.contactfield_set.all()}
        for field in org.datafield_set.visible():
            self.data_field_keys.append(field.key)
            initial = values.get(field.key, None)
            self.fields[field.key] = field.get_form_field(initial=initial)

    def save(self, commit=True):
        # Updating DataField values is managed by a post-save signal.
        field_values = {f: self.cleaned_data.pop(f, None) for f in self.data_field_keys}
        self.instance._data_field_values = field_values
        return super(ContactForm, self).save(commit)
