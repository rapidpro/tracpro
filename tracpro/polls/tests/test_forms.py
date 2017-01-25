from __future__ import unicode_literals

import datetime

import mock

import pytz

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import forms
from .. import models


class TestPollChartFilterForm(TracProTest):

    def setUp(self):
        super(TestPollChartFilterForm, self).setUp()

        self.org = factories.Org()

        # Mock time-dependent utilities so that there is a testable result.
        self.month_range_patcher1 = mock.patch('tracpro.polls.forms.get_month_range')
        self.mock_get_month_range1 = self.month_range_patcher1.start()
        self.mock_get_month_range1.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 3, 1, tzinfo=pytz.UTC),
        )
        self.month_range_patcher2 = mock.patch('tracpro.charts.filters.get_month_range')
        self.mock_get_month_range2 = self.month_range_patcher2.start()
        self.mock_get_month_range2.return_value = (
            datetime.datetime(2016, 2, 1, tzinfo=pytz.UTC),
            datetime.datetime(2016, 3, 1, tzinfo=pytz.UTC),
        )

        # Data to pass to form for testing.
        self.data = {
            'numeric': 'response-rate',
            'date_range': 'custom',
            'start_date': datetime.datetime(2014, 1, 15, tzinfo=pytz.UTC),
            'end_date': datetime.datetime(2014, 10, 22, tzinfo=pytz.UTC),
            'split_regions': False,
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
            'split_regions': False,
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


class TestActivePollsForm(TracProTest):

    @mock.patch.object(models.Poll.objects, 'sync')
    @mock.patch('tracpro.polls.forms.sync_questions_categories')
    def test_active_poll_selection_and_question_sync(self, mock_sync_questions, mock_sync_poll):
        """ Test that the poll questions are being synced after the poll form is saved """
        self.org = factories.Org()
        self.poll_1 = factories.Poll(org=self.org)
        self.poll_2 = factories.Poll(org=self.org)

        # Data to pass to form for testing.
        self.data = {'polls': [self.poll_1.id]}
        self.form = forms.ActivePollsForm(org=self.org, data=self.data)

        self.assertTrue(self.form.is_valid())
        self.form.save()

        self.assertTrue(mock_sync_questions.delay.called)
        self.assertEqual(mock_sync_questions.delay.call_args_list[0][0][0], self.org)
        self.assertEqual(list(mock_sync_questions.delay.call_args_list[0][0][1]), [self.poll_1])
