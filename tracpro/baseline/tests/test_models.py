from datetime import datetime
from dateutil import rrule

from tracpro.test import factories
from tracpro.test.cases import TracProDataTest
from tracpro.polls.models import Answer, Response

from ..models import BaselineTerm


class BaselineTermTest(TracProDataTest):

    def setUp(self):
        """
         There will be a set of results for 3 contacts, in 2 regions
          self.contact1 and self.contact2 are in self.region1
          self.contact4 is in self.region2
        """
        super(BaselineTermTest, self).setUp()

        contacts = [self.contact1, self.contact2, self.contact4]
        self.start_date = datetime(2015, 1, 1, 8)
        self.end_date = datetime(2015, 1, 3, 8)  # Two days of follow up results

        self.baselineterm = BaselineTerm.objects.create(
            org=self.unicef,
            name="Test BaselineTerm",
            start_date=self.start_date,
            end_date=self.end_date,
            baseline_poll=self.poll1,
            baseline_question=self.poll1_question1,
            follow_up_poll=self.poll2,
            follow_up_question=self.poll2_question1
            )

        # Create a single PollRun for the Baseline Poll
        self.baseline_pollrun = factories.RegionalPollRun(
            poll=self.poll1, conducted_on=self.start_date)
        # Create a Response AKA FlowRun for each contact for Baseline
        answer_value = 10  # Baseline values will be 10, 20 and 30
        for contact in contacts:
            response = factories.Response(
                pollrun=self.baseline_pollrun,
                contact=contact,
                created_on=self.start_date,
                updated_on=self.start_date,
                status=Response.STATUS_COMPLETE)
            # Create an Answer for each contact for Baseline
            Answer.objects.create(
                response=response,
                question=self.poll1_question1,
                value=answer_value,
                submitted_on=self.start_date,
                category=u'')
            answer_value += 10  # Increase next answer's value by 10

        # Answers for contacts found in this dictionary
        self.contact_dict = {
            self.contact1: {"answers": [9, 8, 8]},
            self.contact2: {"answers": [15, 10, 10]},
            self.contact4: {"answers": [25, 20, 15]}
        }

        # Create a PollRun for each date from start to end dates for the Follow Up Poll
        date_iter = 0
        for follow_up_date in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            follow_up_pollrun = factories.RegionalPollRun(
                poll=self.poll2, conducted_on=follow_up_date)
            for contact in contacts:
                # Create a Response AKA FlowRun for each contact for Follow Up
                response = factories.Response(
                    pollrun=follow_up_pollrun,
                    contact=contact,
                    created_on=follow_up_date,
                    updated_on=follow_up_date,
                    status=Response.STATUS_COMPLETE)
                answer = self.contact_dict[contact]["answers"][date_iter]
                # Create a randomized Answer for each contact for Follow Up
                Answer.objects.create(
                    response=response,
                    question=self.poll2_question1,
                    value=answer,
                    submitted_on=follow_up_date,
                    category=u'')
            date_iter += 1

    def test_baseline_all_regions(self):
        """ Answers were 10, 20 and 30: Total should be 10 + 20 + 30 = 60 """
        baseline_dict, dates = self.baselineterm.get_baseline(regions=None)

        self.assertEqual(len(baseline_dict), 2)  # Two regions, two sets of baseline values
        # Two answers, 10 + 20 = 30
        self.assertEqual(
            baseline_dict[self.region1.name]["values"],
            [30])
        # One answer, 30 = 30
        self.assertEqual(
            baseline_dict[self.region2.name]["values"],
            [30])

    def test_baseline_single_region(self):
        """ Answers were 10 and 20 for region1 """
        baseline_dict, dates = self.baselineterm.get_baseline(regions=[self.region1])

        self.assertEqual(len(baseline_dict), 1)  # One regions, one baseline
        # Two answers sum = 10 + 20 = 30
        self.assertEqual(
            baseline_dict[self.region1.name]["values"],
            [30])

    def test_baseline_single_region_multiple_answers(self):
        """
        Answers were 10 and 20 for region1
        Add another answer for both region contacts at a later date
        Baseline should be retrieved from all responses
        """
        for contact in [self.contact1, self.contact2]:
            response = factories.Response(
                pollrun=self.baseline_pollrun,
                contact=contact,
                created_on=self.end_date,
                updated_on=self.end_date,
                status=Response.STATUS_COMPLETE)
            Answer.objects.create(
                response=response,
                question=self.poll1_question1,
                value=100,
                submitted_on=self.end_date,
                category=u'')

        baseline_dict, dates = self.baselineterm.get_baseline(regions=[self.region1])

        self.assertEqual(len(baseline_dict), 1)  # One regions, one baseline
        # Two sets of baseline answers
        # sum 1 = 10 + 20 = 30
        # sum 2 = 100 + 100 = 200
        self.assertEqual(
            baseline_dict[self.region1.name]["values"],
            [30, 200])

    def test_follow_up_all_regions(self):
        """
        Region 1 values [9, 8] + [15, 10]  = [24, 18]
        Region 2 values [25, 20]
        """
        follow_ups, dates = self.baselineterm.get_follow_up(regions=None)

        self.assertEqual(len(dates), 3)  # 3 dates
        self.assertEqual(len(follow_ups), 2)  # 2 regions for the follow up dictionary
        # Sum the follow up data for two contacts in Region 1
        self.assertEqual(
            follow_ups[self.region1.name]["values"],
            [24, 18, 18])
        # Data for Region 2 only from one contact
        self.assertEqual(
            follow_ups[self.region2.name]["values"],
            [25, 20, 15])

    def test_follow_up_single_region(self):
        """
        Region 1 values [9, 8] + [15, 10]  = [24, 18]
        Region 2 values [25, 20]
        """
        follow_ups, dates = self.baselineterm.get_follow_up(regions=[self.region2])

        self.assertEqual(len(dates), 3)  # 3 dates
        self.assertEqual(len(follow_ups), 1)  # One region for the follow up dictionary
        # Data for Region 2 only from one contact
        self.assertEqual(
            follow_ups[self.region2.name]["values"],
            [25, 20, 15])
