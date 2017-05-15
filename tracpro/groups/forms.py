from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.client import get_client


class ContactGroupsForm(forms.Form):
    groups = forms.MultipleChoiceField(
        choices=(), label=_("Contact Groups"),
        help_text=_(
            "Contact groups to use."
        ),
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


class PanelsForm(ContactGroupsForm):

    def __init__(self, *args, **kwargs):

        super(PanelsForm, self).__init__(*args, **kwargs)
        self.fields['groups'].help_text = _(
            "Contact groups to track in TracPro as Panels. "
            "To select more than one panel, hold the Control key "
            "(or the Command key on a Macintosh) "
            "while clicking on a panel to add or remove it. "
            "NOTE: TracPro currently supports a one-to-one Contact to Panel Relationship."
            )
        self.fields['groups'].label = _("Panels")


class CohortsForm(ContactGroupsForm):

    def __init__(self, *args, **kwargs):

        super(CohortsForm, self).__init__(*args, **kwargs)
        self.fields['groups'].help_text = _(
            "Contact groups to track in TracPro as Cohorts. "
            "If any contacts in these RapidPro groups "
            "are not also in your selected Panels, they will not be synced in TracPro. "
            "To select more than one cohort, hold the Control key "
            "(or the Command key on a Macintosh) "
            "while clicking on a cohort to add or remove it."
            )
        self.fields['groups'].label = _("Cohorts")
