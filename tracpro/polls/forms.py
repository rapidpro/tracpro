from dateutil.relativedelta import relativedelta

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dash.utils import get_month_range

from . import models


class PollForm(forms.ModelForm):

    class Meta:
        model = models.Poll
        fields = ('name',)


class QuestionForm(forms.ModelForm):

    class Meta:
        model = models.Question
        fields = ('name', 'question_type', 'is_active')


QuestionFormSet = forms.modelformset_factory(
    models.Question,
    form=QuestionForm,
    extra=0,
    can_delete=False)


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


class ChartFilterForm(forms.Form):
    NUMERIC_DATA_CHOICES = (
        ('', ''),
        ('sum', _("Sum of responses")),
        ('average', _("Average of responses")),
        ('response-rate', _("Response rate")),
    )

    DATE_WINDOW_CHOICES = (
        ('', ''),
        ('month', _("Current month")),
        ('30-days', _("Last 30 days")),
        ('60-days', _("Last 60 days")),
        ('90-days', _("Last 90 days")),
        ('6-months', _("Last 6 months")),
        ('12-months', _("Last 12 months")),
        ('custom', _("Custom range...")),
    )

    data_type = forms.ChoiceField(
        label=_("Numeric display"),
        help_text=_("How responses to numeric questions will be charted."),
        choices=NUMERIC_DATA_CHOICES)
    date_range = forms.ChoiceField(
        choices=DATE_WINDOW_CHOICES)
    start_date = forms.DateTimeField(
        required=False,
        widget=forms.widgets.DateInput(attrs={'class': 'datepicker'}),
        error_messages={'invalid': "Please enter a valid date."})
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.widgets.DateInput(attrs={'class': 'datepicker'}),
        error_messages={'invalid': "Please enter a valid date."})

    def __init__(self, *args, **kwargs):
        start_date, end_date = get_month_range()
        kwargs.setdefault('initial', {
            'data_type': 'sum',
            'date_range': 'month',
            'start_date': start_date,
            'end_date': end_date,
        })
        super(ChartFilterForm, self).__init__(*args, **kwargs)

    def clean(self):
        window = self.cleaned_data.get('date_range')
        if window == 'custom':
            # Only apply additional checks if data did not have errors.
            if 'start_date' not in self.errors and 'end_date' not in self.errors:
                start_date = self.cleaned_data.get('start_date')
                end_date = self.cleaned_data.get('end_date')

                # Require at least one date filter.
                if not start_date and not end_date:
                    self.add_error(
                        forms.ALL_FIELDS,
                        _("Please choose a start date or an end date."))

                # Ensure date filter order makes sense.
                elif (start_date and end_date) and start_date > end_date:
                    self.add_error(
                        'end_date',
                        _("End date must be after start date."))

                # Set default values for start date and end date.
                else:
                    self.cleaned_data.setdefault('start_date', None)
                    self.cleaned_data.setdefault('end_date', None)
                    self.data.setdefault('start_date', None)
                    self.data.setdefault('end_date', None)
        else:
            # Throw out user-submitted dates.
            self.cleaned_data.pop('start_date', None)
            self.cleaned_data.pop('end_date', None)
            self.data.pop('start_date', None)
            self.data.pop('end_date', None)
            self._errors.pop('start_date', None)
            self._errors.pop('end_date', None)

            # Calculate the correct date window.
            if window:
                if window == 'month':
                    start_date, end_date = get_month_range()
                else:
                    number, unit = window.split('-')  # e.g., 6-months
                    end_date = timezone.now()
                    start_date = end_date - relativedelta(**{unit: int(number)})
                self.cleaned_data['start_date'] = start_date
                self.cleaned_data['end_date'] = end_date
                self.data['start_date'] = start_date
                self.data['end_date'] = end_date

    def get_value(self, field):
        """Retrieve the validated field value, or its initial value."""
        if not self.is_bound:
            value = self.initial[field]
            return value() if callable(value) else value
        elif self.is_valid():
            return self.cleaned_data[field]
        else:
            raise ValueError("Cannot get value from an invalid form.")
