from django import forms
from django.utils.translation import ugettext_lazy as _

from tracpro.charts import filters
from tracpro.contacts.models import Contact
from tracpro.polls.models import Poll, Question

from .models import BaselineTerm


class BaselineTermForm(forms.ModelForm):
    """ Form for Baseline Term """
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
            polls = Poll.objects.active().by_org(org).order_by('name')
            self.fields['baseline_poll'].queryset = polls
            self.fields['follow_up_poll'].queryset = polls

    def clean(self, *args, **kwargs):
        cleaned_data = super(BaselineTermForm, self).clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                _("Start date should be before end date."))

        baseline_question = cleaned_data.get("baseline_question")
        follow_up_question = cleaned_data.get("follow_up_question")
        if baseline_question and follow_up_question and baseline_question == follow_up_question:
            raise forms.ValidationError(
                _("Baseline and follow up questions should be different."))

        return cleaned_data


class QuestionModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s: %s" % (obj.poll.name, obj.name)


class SpoofDataForm(forms.Form):
    """ Form to create spoofed poll data """
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        help_text=_("Select contacts for this set of spoofed data."))
    start_date = forms.DateField(
        help_text=_("Baseline poll data will be submitted on this date. "
                    "Follow up data will start on this date."))
    end_date = forms.DateField(
        help_text=_("Follow up data will end on this date. "))
    baseline_question = QuestionModelChoiceField(
        queryset=Question.objects.all().order_by('poll__name', 'text'),
        help_text=_("Select a baseline question which will have numeric "
                    "answers only."))
    follow_up_question = QuestionModelChoiceField(
        label=_("Follow Up Question"),
        queryset=Question.objects.all().order_by('poll__name', 'text'),
        help_text=_("Select a follow up question which will have "
                    "numeric answers only."))
    baseline_minimum = forms.IntegerField(
        help_text=_("A baseline answer will be created for each contact "
                    "within the minimum/maximum range."))
    baseline_maximum = forms.IntegerField(
        help_text=_("A baseline answer will be created for each contact "
                    "within the minimum/maximum range."))
    follow_up_minimum = forms.IntegerField(
        label=_("Follow Up Minimum"),
        help_text=_("Follow up answers will be created for each contact "
                    "within the minimum/maximum range."))
    follow_up_maximum = forms.IntegerField(
        label=_("Follow Up Maximum"),
        help_text=_("Follow up answers will be created for each contact "
                    "within the minimum/maximum range."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')

        super(SpoofDataForm, self).__init__(*args, **kwargs)

        if org:
            contacts = Contact.objects.active().by_org(org).order_by('name')
            self.fields['contacts'].queryset = contacts
            questions = Question.objects.filter(poll__in=Poll.objects.active().by_org(org))
            self.fields['baseline_question'].queryset = questions
            self.fields['follow_up_question'].queryset = questions

    def clean(self, *args, **kwargs):
        cleaned_data = super(SpoofDataForm, self).clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                _("Start date should be before end date."))

        baseline_question = cleaned_data.get("baseline_question")
        follow_up_question = cleaned_data.get("follow_up_question")
        if baseline_question and follow_up_question and baseline_question == follow_up_question:
            raise forms.ValidationError(
                _("Baseline and follow up questions should be different."))

        baseline_minimum = cleaned_data.get("baseline_minimum")
        baseline_maximum = cleaned_data.get("baseline_maximum")
        if baseline_minimum and baseline_maximum and baseline_minimum > baseline_maximum:
            raise forms.ValidationError(
                _("Baseline maximum should exceed or equal minimum."))

        follow_up_minimum = cleaned_data.get("follow_up_minimum")
        follow_up_maximum = cleaned_data.get("follow_up_maximum")
        if follow_up_minimum and follow_up_maximum and follow_up_minimum > follow_up_maximum:
            raise forms.ValidationError(
                _("Follow up maximum should exceed or equal minimum."))

        return cleaned_data


class BaselineTermFilterForm(filters.DateRangeFilter, filters.DataFieldFilter,
                             filters.FilterForm):
    goal = forms.FloatField(
        required=False,
        label=_("Goal"),
        help_text=_("If specified, this value will be used instead of "
                    "baseline data."))
    region = forms.ModelChoiceField(
        required=False,
        label=_("Contact region"),
        queryset=None,
        empty_label=_("All regions"),
        help_text=_("If specified, only responses from contacts in this "
                    "region will be shown."))

    def __init__(self, baseline_term, data_regions, *args, **kwargs):
        if not kwargs.get('data'):
            # Set valid data if None (or {}) was provided.
            # Form will always be considered bound.
            kwargs['data'] = {
                'date_range': 'custom',
                'start_date': baseline_term.start_date,
                'end_date': baseline_term.end_date,
            }
        super(BaselineTermFilterForm, self).__init__(*args, **kwargs)

        self.fields['start_date'].required = True
        self.fields['end_date'].required = True

        if data_regions is None:
            queryset = self.org.regions.filter(is_active=True)
        else:
            queryset = data_regions
        queryset = queryset.filter(pk__in=baseline_term.get_regions())
        queryset = queryset.order_by('name')
        self.fields['region'].queryset = queryset

    def filter_contacts(self, queryset=None):
        contacts = super(BaselineTermFilterForm, self).filter_contacts(queryset)
        region = self.cleaned_data.get('region')
        if region:
            contacts = contacts.filter(region=region)
        return contacts
