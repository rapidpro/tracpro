import datetime

import mock

import pytz

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import forms


class TestPollChartFilterForm(TracProTest):

    def setUp(self):
        super(TestPollChartFilterForm, self).setUp()

        self.org = factories.Org()

        # Mock time-dependent utilities so that there is a testable result.
        self.month_range_patcher1 = mock.patch('tracpro.polls.forms.get_month_range')
        self.mock_get_month_range1 = self.month_range_patcher1.start()
        self.mock_get_month_range1.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )
        self.month_range_patcher2 = mock.patch('tracpro.charts.filters.get_month_range')
        self.mock_get_month_range2 = self.month_range_patcher2.start()
        self.mock_get_month_range2.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        )

        # Data to pass to form for testing.
        self.data = {
            'numeric': 'response-rate',
            'date_range': 'custom',
            'start_date': datetime.datetime(2014, 1, 15, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2014, 10, 22, tzinfo=pytz.UTC),
        }

    def tearDown(self):
        super(TestPollChartFilterForm, self).tearDown()
        self.month_range_patcher1.stop()
        self.month_range_patcher2.stop()

    def test_initial(self):
        """Default data should be set if data is not passed to the form."""
        form = forms.PollChartFilterForm(org=self.org)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid())
        self.assertDictEqual(form.data, {
            'numeric': 'sum',
            'date_range': 'month',
            'start_date': datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2016, 2, 29, tzinfo=pytz.UTC),
        })

    def test_numeric_required(self):
        """Data type choice is required."""
        self.data.pop('numeric')
        form = forms.PollChartFilterForm(org=self.org, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'numeric': ['This field is required.'],
        })

    def test_numeric_invalid(self):
        """Data type must come from list of valid choices."""
        self.data['numeric'] = 'invalid'
        form = forms.PollChartFilterForm(org=self.org, data=self.data)
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {
            'numeric': ['Select a valid choice. '
                        'invalid is not one of the available choices.'],
        })
