from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Poll


class PollForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"))

    class Meta:
        model = Poll
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        for question in self.instance.get_questions():
            field_key = '__question__%d__text' % question.pk
            self.fields[field_key] = forms.CharField(
                max_length=255, initial=question.text,
                label=_("Question #%d") % question.order)


class FlowsForm(forms.Form):
    flows = forms.MultipleChoiceField(
        choices=(), label=_("Flows"),
        help_text=_("Flows to track as polls."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')
        super(FlowsForm, self).__init__(*args, **kwargs)
        choices = []
        for flow in org.get_temba_client().get_flows(archived=False):
            choices.append((flow.uuid, flow.name))

        self.fields['flows'].choices = choices
        self.fields['flows'].initial = [p.flow_uuid for p in Poll.get_all(org)]
