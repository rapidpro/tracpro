import copy

from dateutil.relativedelta import relativedelta

import six

from dash.utils import get_month_range

from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from . import fields as filter_fields
from . import utils


class FilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop('org')

        super(FilterForm, self).__init__(*args, **kwargs)

        # Create a shallow copy of the data to ensure that it is
        # mutable. Some filters need the ability to overwrite the
        # data that was passed in.
        if self.data is not None:
            self.data = copy.copy(self.data)


class Filter(six.with_metaclass(DeclarativeFieldsMetaclass, object)):
    # The metaclass is what does the work to set up fields
    # that are declared as attributes of the class.
    pass


class DateRangeFilter(Filter):
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
    start_date = filter_fields.FilterDateField(
        label=_("Start date"),
        required=False)
    end_date = filter_fields.FilterDateField(
        label=_("End date"),
        required=False)

    def clean(self):
        self.cleaned_data = super(DateRangeFilter, self).clean()
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
                    # get_month_range() a tuple with datetimes representing
                    # midnight of the first day of the current month, and
                    # midnight of the first day of the following month.
                    start_date, end_date = get_month_range()

                    # Show the user the last day of the month,
                    # e.g., show June 1 to June 30 rather than June 1 to July 1.
                    end_date = end_date - relativedelta(days=1)
                else:
                    number, unit = window.split('-')  # e.g., 6-months
                    end_date = utils.midnight(timezone.now())
                    start_date = end_date - relativedelta(**{unit: int(number)})

                self.cleaned_data['start_date'] = start_date
                self.cleaned_data['end_date'] = end_date
                self.data['start_date'] = start_date
                self.data['end_date'] = end_date

        # Pad the end_date by one day so that results for all times during
        # the end_date are accounted for in the query.
        end_date = self.cleaned_data.get('end_date')
        if end_date is not None:
            self.cleaned_data['end_date'] = end_date + relativedelta(days=1)

        return self.cleaned_data


class DataFieldFilter(Filter):

    def __init__(self, *args, **kwargs):
        super(DataFieldFilter, self).__init__(*args, **kwargs)
        self.contact_fields = []
        for data_field in self.org.datafield_set.visible():
            field_name = 'contact_{}'.format(data_field.key)
            self.contact_fields.append((field_name, data_field))
            self.fields[field_name] = forms.CharField(
                label='Contact: {}'.format(data_field.display_name),
                required=False)

    def filter_contacts(self, queryset=None):
        """Filter queryset to match all contact field search input."""
        contacts = queryset if queryset is not None else self.org.contacts.all()
        for name, data_field in self.contact_fields:
            value = self.cleaned_data.get(name)
            if value:
                contacts = contacts.filter(
                    contactfield__field=data_field,
                    contactfield__value__icontains=value)
        return contacts
