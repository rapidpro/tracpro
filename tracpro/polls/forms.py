from django import forms
from django.utils.translation import ugettext_lazy as _

from . import models


class PollForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"))

    class Meta:
        model = models.Poll
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        for question in self.instance.get_questions():
            field_key = '__question__%d__text' % question.pk
            self.fields[field_key] = forms.CharField(
                max_length=255, initial=question.display_name,
                label=_("Question #%d") % question.order)


class ActivePollsForm(forms.Form):
    """Set which polls should be synced with RapidPro."""
    polls = forms.ModelMultipleChoiceField(
        queryset=None, required=False, label=_("Active flows"),
        help_text=_("Flows to track as polls."))

    def __init__(self, org, *args, **kwargs):
        self.org = org
        super(ActivePollsForm, self).__init__(*args, **kwargs)

        # Make sure we have the most up-to-date Poll info.
        # NOTE: This makes an in-band request to an external API.
        models.Poll.objects.sync(self.org)

        polls = models.Poll.objects.by_org(self.org)
        self.fields['polls'].queryset = polls
        self.fields['polls'].initial = polls.active()

    def save(self):
        uuids = self.cleaned_data['polls'].values_list('flow_uuid', flat=True)
        models.Poll.objects.set_active_for_org(self.org, uuids)
