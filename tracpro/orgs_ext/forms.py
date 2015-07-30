from django import forms
from django.utils.translation import ugettext_lazy as _

from dash.orgs.forms import OrgForm
from dash.orgs.models import Org


class OrgExtForm(OrgForm):
    facility_code_field = forms.ChoiceField(
        choices=(), label=_("Facility code field"),
        help_text=_("Contact field to use as the facility code."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')
        super(OrgExtForm, self).__init__(*args, **kwargs)
        field_choices = []
        for field in org.get_temba_client().get_fields():
            field_choices.append((field.key, "%s (%s)" % (field.label, field.key)))
        self.fields['facility_code_field'].choices = field_choices
        self.fields['facility_code_field'].initial = org.get_facility_code_field()

    class Meta:
        model = Org
        fields = forms.ALL_FIELDS
