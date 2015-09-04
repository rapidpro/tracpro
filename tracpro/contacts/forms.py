from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.groups.models import Group, Region

from .fields import URNField
from .models import Contact


class ContactForm(forms.ModelForm):
    name = forms.CharField(max_length=128, label=_("Full name"))
    urn = URNField(
        label=_("Phone/Twitter"),
        help_text=_("Phone number or Twitter handle of this contact."))
    region = forms.ModelChoiceField(
        label=_("Region"),
        queryset=Region.objects.none(),
        help_text=_("Region where this contact lives."))
    group = forms.ModelChoiceField(
        label=_("Reporter Group"),
        queryset=Group.objects.none(),
        help_text=_("Reporter Group to which this contact belongs."))
    facility_code = forms.CharField(
        label=_("Facility Code"), max_length=16, required=False)
    language = forms.CharField(
        label=_("Language"), required=False,
        widget=forms.TextInput(attrs={'class': 'language-field'}))

    class Meta:
        model = Contact
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ContactForm, self).__init__(*args, **kwargs)
        org = self.user.get_org()
        self.fields['region'].queryset = self.user.get_direct_regions(org).order_by('name')
        self.fields['group'].queryset = Group.get_all(org).order_by('name')
