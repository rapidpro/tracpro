from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.polls.models import Poll, Question
from tracpro.contacts.models import Contact
from .models import BaselineTerm


class BaselineTermForm(forms.ModelForm):
    """
    Form for Baseline Term
    """
    class Meta:
        model = BaselineTerm
        fields = ('name', 'org', 'start_date', 'end_date',
                  'baseline_poll', 'baseline_question',
                  'follow_up_poll', 'follow_up_question',
                  'y_axis_title')

        widgets = {
            'start_date': forms.widgets.DateInput(attrs={'class': 'datepicker'}),
            'end_date': forms.widgets.DateInput(attrs={'class': 'datepicker'}),
            'org': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        org = self.user.get_org()

        super(BaselineTermForm, self).__init__(*args, **kwargs)

        if org:
            polls = Poll.get_all(org).order_by('name')
            self.fields['baseline_poll'].queryset = polls
            self.fields['follow_up_poll'].queryset = polls

    def clean(self, *args, **kwargs):
        cleaned_data = super(BaselineTermForm, self).clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "Start date should be before end date."
            )

        baseline_question = cleaned_data.get("baseline_question")
        follow_up_question = cleaned_data.get("follow_up_question")
        if baseline_question and follow_up_question and baseline_question == follow_up_question:
            raise forms.ValidationError(
                "Baseline question and follow up question should be different."
            )

        return cleaned_data


class QuestionModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s: %s" % (obj.poll.name, obj.text)


class SpoofDataForm(forms.Form):
    """
    Form to create spoofed poll data
    """
    contacts = forms.ModelMultipleChoiceField(queryset=Contact.objects.all(),
                                              help_text=_("Select contacts for this set of spoofed data."))
    start_date = forms.DateField(help_text=_(
        "Baseline poll data will be submitted on this date. "
        "Follow up data will start on this date."))
    end_date = forms.DateField(help_text=_(
        "Follow up data will end on this date. "
        "If dates go beyond 1 week, a second set of baseline answers will be created."))
    baseline_question = QuestionModelChoiceField(queryset=Question.objects.all().order_by('poll__name', 'text'),
                                                 help_text=_("Select a baseline question which " +
                                                             "will have numeric answers only."))
    follow_up_question = QuestionModelChoiceField(queryset=Question.objects.all().order_by('poll__name', 'text'),
                                                  help_text=_("Select a follow up question which " +
                                                              "will have numeric answers only."))
    baseline_minimum = forms.IntegerField(
        help_text=_("A baseline answer will be created for each contact within the minimum/maximum range."))
    baseline_maximum = forms.IntegerField(
        help_text=_("A baseline answer will be created for each contact within the minimum/maximum range."))
    follow_up_minimum = forms.IntegerField(
        help_text=_("Follow up answers will be created for each contact within the minimum/maximum range."))
    follow_up_maximum = forms.IntegerField(
        help_text=_("Follow up answers will be created for each contact within the minimum/maximum range."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')

        super(SpoofDataForm, self).__init__(*args, **kwargs)

        if org:
            contacts = Contact.get_all(org).order_by('name')
            self.fields['contacts'].queryset = contacts
            questions = Question.objects.filter(poll__in=Poll.get_all(org))
            self.fields['baseline_question'].queryset = questions
            self.fields['follow_up_question'].queryset = questions

    def clean(self, *args, **kwargs):
        cleaned_data = super(SpoofDataForm, self).clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "Start date should be before end date."
            )

        baseline_question = cleaned_data.get("baseline_question")
        follow_up_question = cleaned_data.get("follow_up_question")
        if baseline_question and follow_up_question and baseline_question == follow_up_question:
            raise forms.ValidationError(
                "Baseline question and follow up question should be different."
            )

        baseline_minimum = cleaned_data.get("baseline_minimum")
        baseline_maximum = cleaned_data.get("baseline_maximum")
        if baseline_minimum and baseline_maximum and baseline_minimum > baseline_maximum:
            raise forms.ValidationError(
                "Baseline minimum should be lower than maximum."
            )

        follow_up_minimum = cleaned_data.get("follow_up_minimum")
        follow_up_maximum = cleaned_data.get("follow_up_maximum")
        if follow_up_minimum and follow_up_maximum and follow_up_minimum > follow_up_maximum:
            raise forms.ValidationError(
                "Follow up minimum should be lower than maximum."
            )

        return cleaned_data
