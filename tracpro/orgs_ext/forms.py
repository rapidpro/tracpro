from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from dash.orgs.forms import OrgForm

from tracpro.contacts.models import DataField


class OrgExtForm(OrgForm):
    """Also configure available languages for this organization.

    The motivation is that given a many-org (i.e., country) installation,
    the global list of languages could get very long.
    Each org is probably interested in seeing only a subset of those languages.
    """

    available_languages = forms.MultipleChoiceField(
        choices=settings.LANGUAGES,
        help_text=_("The languages used by administrators in your organization"))
    contact_fields = forms.MultipleChoiceField(
        choices=[], required=False,
        help_text=_("Custom contact data fields that should be visible "
                    "and editable in TracPro."))

    def __init__(self, *args, **kwargs):
        super(OrgExtForm, self).__init__(*args, **kwargs)

        # Modify the language field to better match our usage.
        language = self.fields['language']
        language.required = True
        language.label = _("Default language")
        language.help_text = _("The default language for your organization")

        # available_languages is a config field so must be set explicitly.
        self.fields['available_languages'].initial = self.instance.available_languages or []

        if not self.instance.pk:
            # We don't have this org's API key yet,
            # so we can't get available fields from the RapidPro API.
            self.fields.pop('contact_fields')
        else:
            # Make sure we have the most up-to-date field information.
            # NOTE: This makes an in-band request to an external API.
            DataField.objects.sync(self.instance)

            queryset = self.instance.datafield_set.all()
            choices = [(f.key, f.display_name) for f in queryset]
            initial = list(queryset.visible().values_list('key', flat=True))
            self.fields['contact_fields'].choices = choices
            self.fields['contact_fields'].initial = initial

    def clean(self):
        """Ensure the default language is chosen from the available languages."""
        language = self.cleaned_data.get('language')
        available_languages = self.cleaned_data.get('available_languages') or []
        if language and available_languages:  # otherwise, default errors are preferred
            if language not in available_languages:
                raise forms.ValidationError(
                    _("Default language must be one of the languages available "
                      "for this organization."))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        # Set the available_languages config field.
        if 'available_languages' in self.fields:
            available_languages = self.cleaned_data.get('available_languages')
            self.instance.available_languages = available_languages or []

        if 'contact_fields' in self.fields:
            # Set hook that will be picked up by a post-save signal.
            self.instance._visible_data_fields = self.cleaned_data.get('contact_fields')

        return super(OrgExtForm, self).save(*args, **kwargs)


class SimpleOrgEditForm(OrgForm):
    facility_code_field = forms.ChoiceField(
        choices=(), label=_("Facility code field"),
        help_text=_("Contact field to use as the facility code."))

    class Meta(OrgForm.Meta):
        fields = ('name', 'timezone')

    def __init__(self, *args, **kwargs):
        super(SimpleOrgEditForm, self).__init__(*args, **kwargs)
        field_choices = [(f.key, '{} ({})'.format(f.label, f.key))
                         for f in self.instance.get_temba_client().get_fields()]
        self.fields['facility_code_field'].choices = field_choices
        self.fields['facility_code_field'].initial = self.instance.facility_code_field

    def save(self, *args, **kwargs):
        self.instance.facility_code_field = self.cleaned_data['facility_code_field']
        return super(SimpleOrgEditForm, self).save(*args, **kwargs)
