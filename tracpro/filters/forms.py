from dateutil.relativedelta import relativedelta

from dash.utils import get_month_range

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class DateRangeFilterForm(forms.Form):
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

    date_range = forms.ChoiceField(
        label=_("Date range"),
        choices=DATE_WINDOW_CHOICES)
    start_date = forms.DateTimeField(
        label=_("Start date"),
        required=False,
        widget=forms.widgets.DateInput(attrs={'class': 'datepicker'}),
        error_messages={'invalid': "Please enter a valid date."})
    end_date = forms.DateTimeField(
        label=_("End date"),
        required=False,
        widget=forms.widgets.DateInput(attrs={'class': 'datepicker'}),
        error_messages={'invalid': "Please enter a valid date."})

    def clean(self):
        self.cleaned_data = super(DateRangeFilterForm, self).clean()
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
        return self.cleaned_data


class DataFieldFilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop('org')
        self.contact_fields = []
        for data_field in self.org.datafield_set.visible():
            field_name = 'contact_{}'.format(data_field.key)
            self.contact_fields.append((field_name, data_field))
            self.base_fields[field_name] = forms.CharField(
                label='Contact: {}'.format(data_field.display_name),
                required=False)

        super(DataFieldFilterForm, self).__init__(*args, **kwargs)
