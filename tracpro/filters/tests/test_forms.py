import datetime

from dateutil.relativedelta import relativedelta

import mock

import pytz

from django.forms import ALL_FIELDS

from tracpro.test.cases import TracProTest

from .. import forms


class TestDateRangeFilterForm(TracProTest):

    def setUp(self):
        super(TestDateRangeFilterForm, self).setUp()

        # Mock time-dependent utilities so that there is a testable result.
        self.month_range_patcher = mock.patch('tracpro.filters.forms.get_month_range')
        self.mock_get_month_range = self.month_range_patcher.start()
        self.mock_get_month_range.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )

        self.now_patcher = mock.patch('tracpro.filters.forms.timezone.now')
        self.mock_now = self.now_patcher.start()
        self.mock_now.return_value = datetime.datetime(2016, 2, 15, tzinfo=pytz.UTC)

        # Data to pass to form for testing.
        self.data = {
            'date_range': 'custom',
            'start_date': datetime.datetime(2014, 1, 15, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2014, 10, 22, tzinfo=pytz.UTC),
        }

    def tearDown(self):
        super(TestDateRangeFilterForm, self).tearDown()
        self.month_range_patcher.stop()
        self.now_patcher.stop()

    def _check_data(self, form, date_range, start_date, end_date):
        """Check that the form is valid and has the expected data."""
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date_range'], date_range)
        self.assertEqual(form.data['start_date'], start_date)
        self.assertEqual(form.cleaned_data['start_date'], start_date)
        self.assertEqual(form.data['end_date'], end_date)
        self.assertEqual(form.cleaned_data['end_date'], end_date)

    def test_date_range_required(self):
        """Date range choice is required."""
        self.data.pop('date_range')
        form = forms.DateRangeFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'date_range': ['This field is required.'],
        })

    def test_date_range_invalid(self):
        """Date range must come from a list of valid choices."""
        self.data['date_range'] = 'invalid'
        form = forms.DateRangeFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'date_range': ['Select a valid choice. '
                           'invalid is not one of the available choices.'],
        })

        # Start and end date values should be invalidated and removed from the data.
        self.assertNotIn('start_date', form.cleaned_data)
        self.assertNotIn('end_date', form.cleaned_data)
        self.assertNotIn('start_date', form.data)
        self.assertNotIn('end_date', form.data)

    def test_clean__month(self):
        """Set start and end dates appropriately if month is specified."""
        self.data['date_range'] = 'month'
        self._check_data(
            form=forms.DateRangeFilterForm(data=self.data),
            date_range='month',
            start_date=datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            end_date=datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )

    def test_clean__predefined_range(self):
        """Set start and end dates appropriately for predefined date range."""
        tests = (
            (30, 'days'),
            (60, 'days'),
            (90, 'days'),
            (6, 'months'),
            (12, 'months'),
        )
        for number, unit in tests:
            choice = '{}-{}'.format(number, unit)
            self.data['date_range'] = choice
            end_date = datetime.datetime(2016, 2, 15, tzinfo=pytz.UTC)
            self._check_data(
                form=forms.DateRangeFilterForm(data=self.data),
                date_range=choice,
                end_date=end_date,
                start_date=end_date - relativedelta(**{unit: number}),
            )

    def test_clean__predefined_range__date_error(self):
        """Discard date errors if predefined date range is selected."""
        self.data['start_date'] = 'invalid'
        self.data['end_date'] = 'invalid'
        self.data['date_range'] = 'month'
        self._check_data(
            form=forms.DateRangeFilterForm(data=self.data),
            date_range='month',
            start_date=datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            end_date=datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )

    def test_clean__custom_date_range(self):
        """Do not reset start and end dates if custom date range is specified."""
        self._check_data(
            form=forms.DateRangeFilterForm(data=self.data),
            date_range='custom',
            start_date=self.data['start_date'],
            end_date=self.data['end_date'],
        )

    def test_clean__custom_date_range__no_end_date(self):
        self.data.pop('end_date')
        self._check_data(
            form=forms.DateRangeFilterForm(data=self.data),
            date_range='custom',
            start_date=self.data['start_date'],
            end_date=None,
        )

    def test_clean__custom_date_range__no_start_date(self):
        self.data.pop('start_date')
        self._check_data(
            form=forms.DateRangeFilterForm(data=self.data),
            date_range='custom',
            start_date=None,
            end_date=self.data['end_date'],
        )

    def test_clean__custom_date_range__invalid_start_end_dates(self):
        """Don't apply additional checks if start or end dates are invalid."""
        self.data['start_date'] = 'invalid'
        self.data['end_date'] = 'invalid'
        form = forms.DateRangeFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'start_date': ["Please enter a valid date."],
            'end_date': ["Please enter a valid date."],
        })

    def test_clean__custom_date_range_requires_dates(self):
        """Either start and end date must be specified for a custom date range."""
        self.data.pop('end_date')
        self.data.pop('start_date')
        form = forms.DateRangeFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            ALL_FIELDS: ["Please choose a start date or an end date."],
        })

    def test_clean__custom_date_range_date_order(self):
        """Start date must come before end date."""
        start_date, end_date = self.data['start_date'], self.data['end_date']
        self.data['end_date'], self.data['start_date'] = start_date, end_date
        form = forms.DateRangeFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'end_date': ["End date must be after start date."],
        })
