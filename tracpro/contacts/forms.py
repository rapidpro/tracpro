from uuid import uuid4

from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.groups.models import Group, Region
from tracpro.groups.fields import ModifiedLevelTreeNodeChoiceField

from .fields import URNField
from .models import Contact


class ContactForm(forms.ModelForm):
    urn = URNField(label=_("Phone/Twitter"))
    region = ModifiedLevelTreeNodeChoiceField(
        label=_("Region"), empty_label="", queryset=Region.objects.none())

    class Meta:
        model = Contact
        fields = forms.ALL_FIELDS
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

            # Since we are creating this contact (rather than RapidPro),
            # we must create a UUID for it.
            self.instance.uuid = str(uuid4())

        self.fields['name'].required = True
        self.fields['group'].required = True

        self.fields['region'].queryset = self.user.get_all_regions(org)
        self.fields['group'].empty_label = ""
        self.fields['group'].queryset = Group.get_all(org).order_by('name')
