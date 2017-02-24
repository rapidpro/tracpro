from __future__ import unicode_literals

from dash.orgs.forms import OrgForm
from django.contrib.auth.models import User

from temba_client.base import TembaAPIError

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from tracpro.contacts.models import DataField

from . import utils


class UserMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, user):
        """
        Display a user as their full name from their profile,
        if they have one, else "No profile", and then add on
        their email to distinguish multiple accounts under the
        same full name (or no profile).
        """
        try:
            full_name = user.profile.full_name
        except User.profile.RelatedObjectDoesNotExist:
            full_name = "No profile"

        return "{full_name} ({email})".format(
            full_name=full_name,
            email=user.email
        )


class OrgExtForm(OrgForm):
    """Also configure available languages for this organization.

    The motivation is that given a many-org (i.e., country) installation,
    the global list of languages could get very long.
    Each org is probably interested in seeing only a subset of those languages.
    """

    available_languages = forms.MultipleChoiceField(
        choices=settings.LANGUAGES,  # Rely on settings to be in a useful order.
        help_text=_("The languages used by administrators in your organization"),
        widget=forms.widgets.SelectMultiple(attrs={'size': str(len(settings.LANGUAGES))}),
    )
    show_spoof_data = forms.BooleanField(
        required=False,
        help_text=_("Whether to show spoof data for this organization."))
    contact_fields = forms.ModelMultipleChoiceField(
        queryset=None, required=False,
        help_text=_("Custom contact data fields that should be visible "
                    "and editable in TracPro."),
        widget=forms.widgets.SelectMultiple(attrs={'size': '20'}),
    )
    administrators = UserMultipleChoiceField(
        queryset=None,  # OrgForm.__init__ will set this
        widget=forms.widgets.SelectMultiple(attrs={'size': '20'}),
        help_text=_("The administrators for this organization")
    )

    def __init__(self, *args, **kwargs):
        super(OrgExtForm, self).__init__(*args, **kwargs)

        # Modify the language field to better match our usage.
        language = self.fields['language']
        language.required = True
        language.label = _("Default language")
        language.help_text = _("The default language for your organization")

        # All orgs must use a subdomain.
        self.fields['subdomain'].required = True

        # Config field values are not set automatically.
        self.fields['available_languages'].initial = self.instance.available_languages or []
        self.fields['show_spoof_data'].initial = self.instance.show_spoof_data or False

        # Sort the administrators
        self.fields['administrators'].queryset \
            = self.fields['administrators'].queryset.order_by('profile__full_name')

        if not self.instance.pk:
            # We don't have this org's API key yet,
            # so we can't get available fields from the RapidPro API.
            self.fields.pop('contact_fields')
        else:
            try:
                # Make sure we have the most up-to-date DataField info.
                # NOTE: This makes an in-band request to an external API.
                DataField.objects.sync(self.instance)
            except TembaAPIError as e:
                if utils.caused_by_bad_api_key(e):
                    # Org has an invalid API key, but user needs to be
                    # able to access this form in order to update it.
                    pass
                else:
                    raise

            data_fields = self.instance.datafield_set.all()
            self.fields['contact_fields'].queryset = data_fields.order_by('label')
            self.fields['contact_fields'].initial = data_fields.visible()

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
        # Config field values are not set automatically.
        if 'available_languages' in self.fields:
            available_languages = self.cleaned_data.get('available_languages')
            self.instance.available_languages = available_languages or []
        if 'show_spoof_data' in self.fields:
            show_spoof_data = self.cleaned_data.get('show_spoof_data')
            self.instance.show_spoof_data = show_spoof_data or False

        if 'contact_fields' in self.fields:
            # Set hook that will be picked up by a post-save signal.
            # Must be done post-save to avoid making changes if any earlier
            # part of the transaction fails.
            self.instance._visible_data_fields = self.cleaned_data.get('contact_fields')

        return super(OrgExtForm, self).save(*args, **kwargs)


class FetchRunsForm(forms.Form):
    days = forms.IntegerField(initial=1, min_value=1)
