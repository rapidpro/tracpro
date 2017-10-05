from __future__ import unicode_literals

import datetime

from dateutil.relativedelta import relativedelta

import pytz

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from ..charts import chart_baseline
from ..forms import BaselineTermFilterForm
from ..models import BaselineTerm


class TestChartBaseline(TracProTest):

    def setUp(self):
        super(TestChartBaseline, self).setUp()

        self.org = factories.Org()

        self.contact1 = factories.Contact(org=self.org, name="Apple")
        self.contact2 = factories.Contact(org=self.org, name="Blueberry")
        self.contact3 = factories.Contact(org=self.org, name="Cherry")

        self.start_date = datetime.datetime(2015, 1, 1, 8, tzinfo=pytz.utc)

        self.baseline = factories.Question(poll__org=self.org)
        self.baseline_pollrun1 = factories.UniversalPollRun(
            poll=self.baseline.poll,
            conducted_on=self.start_date)
        self.baseline_pollrun2 = factories.UniversalPollRun(
            poll=self.baseline.poll,
            conducted_on=self.start_date + relativedelta(days=1))

        self.follow_up = factories.Question(poll__org=self.org)
        self.follow_up_pollrun1 = factories.UniversalPollRun(
            poll=self.follow_up.poll,
            conducted_on=self.start_date + relativedelta(days=1))
        self.follow_up_pollrun2 = factories.UniversalPollRun(
            poll=self.follow_up.poll,
            conducted_on=self.start_date + relativedelta(days=2))
        self.follow_up_pollrun3 = factories.UniversalPollRun(
            poll=self.follow_up.poll,
            conducted_on=self.start_date + relativedelta(days=3))

        self.baseline_term = BaselineTerm.objects.create(
            org=self.org,
            name="Test Baseline Term",
            start_date=self.start_date,
            end_date=self.start_date + relativedelta(days=3),
            baseline_poll=self.baseline.poll,
            baseline_question=self.baseline,
            follow_up_poll=self.follow_up.poll,
            follow_up_question=self.follow_up,
            y_axis_title="# cats")

        # Create an answer for each contact.
        contacts = [self.contact1, self.contact2, self.contact3]
        for i, contact in enumerate(contacts, 1):
            for j, pollrun in enumerate(self.baseline.poll.pollruns.all(), 1):
                factories.Answer(
                    response__contact=contact,
                    response__pollrun=pollrun,
                    question=self.baseline,
                    value=10 * i * j,
                    submitted_on=self.start_date + relativedelta(days=j - 1))

            for j, pollrun in enumerate(self.follow_up.poll.pollruns.all(), 1):
                factories.Answer(
                    response__contact=contact,
                    response__pollrun=pollrun,
                    question=self.follow_up,
                    value=7 * i * j,
                    submitted_on=self.start_date + relativedelta(days=j))

        # Empty filter form for testing.
        self.filter_form = BaselineTermFilterForm(
            org=self.org, baseline_term=self.baseline_term, data_regions=None)

    def get_data(self, region, include_subregions, assert_empty=False):
        """Get data and transform for easy testing."""
        self.filter_form.full_clean()
        chart_data, summary_table = chart_baseline(
            baseline_term=self.baseline_term,
            filter_form=self.filter_form,
            region=region,
            include_subregions=include_subregions)

        if assert_empty:
            self.assertIsNone(chart_data)
            self.assertIsNone(summary_table)

        self.assertEqual(set(chart_data.keys()), set(['series', 'categories']))

        series = {s['name']: s['data'] for s in chart_data['series']}
        categories = chart_data['categories']
        summary_data = dict(summary_table)

        return series, categories, summary_data

    def test_chart_data__universal(self):
        series, categories, summary_data = self.get_data(region=None, include_subregions=True)

        # There should be 3 dates to match each follow-up pollrun.
        self.assertEqual(categories, [
            "2015-01-02",
            "2015-01-03",
            "2015-01-04",
        ])

        self.assertEqual(summary_data['Dates'], 'January 01, 2015 - January 04, 2015')
        self.assertEqual(summary_data['Baseline response rate (%)'], 100)
        self.assertEqual(summary_data['Baseline value (# cats)'], 60.0)
        self.assertEqual(summary_data['Follow up mean (# cats)'], 84.0)
        self.assertEqual(summary_data['Follow up standard deviation'], 34.3)
        self.assertEqual(summary_data['Follow up response rate (%)'], 100)

        # Baseline should be sum of first answers per contact.
        # Series length should match that of follow-up.
        # 10 + 20 + 30 = 60
        self.assertEqual(series['Baseline'], [60.0, 60.0, 60.0])

        # Follow-up should be sum of contact answers per pollrun.
        self.assertEqual(series['Follow up'], [
            {'y': 42.0},  # 7 + 14 + 21
            {'y': 84.0},  # 14 + 28 + 42
            {'y': 126.0},  # 21 + 42 + 63
        ])

    def test_chart_data__with_user_goal(self):
        user_goal = 666
        self.filter_form.data['goal'] = user_goal
        series, categories, summary_data = self.get_data(region=None, include_subregions=True)

        # There should be 3 dates to match each follow-up pollrun.
        self.assertEqual(categories, [
            "2015-01-02",
            "2015-01-03",
            "2015-01-04",
        ])

        self.assertEqual(summary_data['Dates'], 'January 01, 2015 - January 04, 2015')
        self.assertIsNone(summary_data['Baseline response rate (%)'])
        self.assertEqual(summary_data['Baseline value (# cats)'], user_goal)
        self.assertEqual(summary_data['Follow up mean (# cats)'], 84.0)
        self.assertEqual(summary_data['Follow up standard deviation'], 34.3)
        self.assertEqual(summary_data['Follow up response rate (%)'], 100)

        # Series length should match that of follow-up.
        # 10 + 20 + 30 = 60
        self.assertEqual(series['Baseline'], [user_goal, user_goal, user_goal])

        # Follow-up should be sum of contact answers per pollrun.
        self.assertEqual(series['Follow up'], [
            {'y': 42.0},  # 7 + 14 + 21
            {'y': 84.0},  # 14 + 28 + 42
            {'y': 126.0},  # 21 + 42 + 63
        ])
