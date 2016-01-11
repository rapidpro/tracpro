import datetime

import mock

import pytz

from tracpro.test.cases import TracProTest

from .. import forms


class TestChartFilterForm(TracProTest):

    def setUp(self):
        super(TestChartFilterForm, self).setUp()

        # Mock time-dependent utilities so that there is a testable result.
        self.month_range_patcher = mock.patch('tracpro.polls.forms.get_month_range')
        self.mock_get_month_range = self.month_range_patcher.start()
        self.mock_get_month_range.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )

        self.now_patcher = mock.patch('tracpro.polls.forms.timezone.now')
        self.mock_now = self.now_patcher.start()
        self.mock_now.return_value = datetime.datetime(2016, 2, 15, tzinfo=pytz.UTC)

        # Data to pass to form for testing.
        self.data = {
            'data_type': 'response-rate',
            'date_range': 'custom',
            'start_date': datetime.datetime(2014, 1, 15, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2014, 10, 22, tzinfo=pytz.UTC),
        }

        # Expected initial values.
        self.expected_initial = {
            'data_type': 'sum',
            'date_range': 'month',
            'start_date': datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        }

    def tearDown(self):
        super(TestChartFilterForm, self).tearDown()
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

    def test_initial(self):
        """Initial values should be set for form fields."""
        form = forms.ChartFilterForm()
        for field, value in self.expected_initial.items():
            self.assertIsNone(form.fields[field].initial)
            self.assertEqual(form.initial[field], value)

    def test_get_value__form_unbound(self):
        """get_value() should return field's initial valid if form is unbound."""
        form = forms.ChartFilterForm()
        self.assertFalse(form.is_bound)
        for field, value in self.expected_initial.items():
            self.assertEqual(form.get_value(field), value)

    def test_get_value__form_invalid(self):
        """get_value() cannot be called on an invalid form."""
        form = forms.ChartFilterForm(data={})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        for field in self.data.keys():
            with self.assertRaises(ValueError):
                form.get_value('data_type')

    def test_get_value__field_nonexistant(self):
        """get_value() should raise a KeyError if requested field is not in form."""
        form = forms.ChartFilterForm(data=self.data)
        self.assertTrue(form.is_valid())
        with self.assertRaises(KeyError):
            form.get_value('invalid')

    def test_get_value__form_valid(self):
        """get_value() should return the passed-in value for a valid form."""
        form = forms.ChartFilterForm(data=self.data)
        for field, value in self.data.items():
            self.assertEqual(form.get_value(field), value)

    def test_data_type_required(self):
        """Data type choice is required."""
        self.data.pop('data_type')
        form = forms.ChartFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'data_type': ['This field is required.'],
        })

    def test_data_type_invalid(self):
        """Data type must come from list of valid choices."""
        self.data['data_type'] = 'invalid'
        form = forms.ChartFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'data_type': ['Select a valid choice. '
                          'invalid is not one of the available choices.'],
        })

    def test_date_range_required(self):
        """Date range choice is required."""
        self.data.pop('date_range')
        form = forms.ChartFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'date_range': ['This field is required.'],
        })

    def test_date_range_invalid(self):
        """Date range must come from a list of valid choices."""
        self.data['date_range'] = 'invalid'
        form = forms.ChartFilterForm(data=self.data)
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
        form = forms.ChartFilterForm(data=self.data)
        self._check_data(
            form, 'month',
            start_date=datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            end_date=datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC))

    def test_clean__predefined_range(self):
        """Set start and end dates appropriately for predefined date range."""
        for days in (30, 60, 90):
            self.data['date_range'] = days
            form = forms.ChartFilterForm(data=self.data)
            end_date = datetime.datetime(2016, 2, 15, tzinfo=pytz.UTC)
            self._check_data(
                form, str(days), end_date=end_date,
                start_date=end_date - datetime.timedelta(days=days))

    def test_clean__custom_date_range(self):
        """Do not reset start and end dates if custom date range is specified."""
        form = forms.ChartFilterForm(data=self.data)
        self._check_data(
            form, 'custom',
            end_date=datetime.datetime(2014, 10, 22, tzinfo=pytz.UTC),
            start_date=datetime.datetime(2014, 1, 15, tzinfo=pytz.UTC))

    def test_clean__custom_date_range_requires_dates(self):
        """Both start and end date must be specified for a custom date range."""
        self.data.pop('end_date')
        self.data.pop('start_date')
        form = forms.ChartFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'start_date': ["Please select a start date."],
            'end_date': ["Please select an end date."],
        })

    def test_clean__custom_date_range_date_order(self):
        """Start date must come before end date."""
        start_date, end_date = self.data['start_date'], self.data['end_date']
        self.data['end_date'], self.data['start_date'] = start_date, end_date
        form = forms.ChartFilterForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'end_date': ["End date must be after start date."],
        })
