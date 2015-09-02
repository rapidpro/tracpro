from datetime import datetime
from dateutil import rrule

from tracpro.test.cases import TracProDataTest
from ..models import BaselineTerm
from tracpro.polls.models import (
    Answer, PollRun, Response, RESPONSE_COMPLETE
)


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
        self.end_date = datetime(2015, 1, 2, 8)  # Two days of follow up results

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
        baseline_pollrun = PollRun.objects.create(poll=self.poll1, conducted_on=self.start_date)
        # Create a Response AKA FlowRun for each contact for Baseline
        answer_value = 10  # Baseline values will be 10, 20 and 30
        for contact in contacts:
            response = Response.objects.create(
                pollrun=baseline_pollrun,
                contact=contact,
                created_on=self.start_date,
                updated_on=self.start_date,
                status=RESPONSE_COMPLETE,
                is_active=True)
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
            self.contact1: {"answers": [9, 8]},
            self.contact2: {"answers": [15, 10]},
            self.contact4: {"answers": [25, 20]}
        }
        """
        # Create a PollRun for each date from start to end dates for the Follow Up Poll
        for follow_up_date in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            follow_up_pollrun = PollRun.objects.create(
                poll=self.poll2, conducted_on=follow_up_date)
        """
        # Create a PollRun for each date from start to end dates for the Follow Up Poll
        date_iter = 0
        for follow_up_date in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            follow_up_pollrun = PollRun.objects.create(
                poll=self.poll2, conducted_on=follow_up_date)
            for contact in contacts:
                # Create a Response AKA FlowRun for each contact for Follow Up
                response = Response.objects.create(
                    pollrun=follow_up_pollrun,
                    contact=contact,
                    created_on=follow_up_date,
                    updated_on=follow_up_date,
                    status=RESPONSE_COMPLETE,
                    is_active=True)
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
        baseline_dict = self.baselineterm.get_baseline(region=None)

        self.assertEqual(len(baseline_dict), 2)  # Two regions, two sets of baseline values
        # Two answers, 10 + 20 = 30
        self.assertEqual(
            baseline_dict[self.region1.name]["values"],
            30)
        # One answer, 30 = 30
        self.assertEqual(
            baseline_dict[self.region2.name]["values"],
            30)

    def test_baseline_region_1(self):
        """ Answers were 10 and 20 for region1 """
        baseline_dict = self.baselineterm.get_baseline(region=self.region1)

        self.assertEqual(len(baseline_dict), 1)  # One regions, one baseline
        # Two answers sum = 10 + 20 = 30
        self.assertEqual(
            baseline_dict[self.region1.name]["values"],
            30)

    def test_follow_up(self):
        """
        Region 1 values [9, 8] + [15, 10]  = [24, 18]
        Region 2 values [25, 20]
        """
        follow_ups, dates = self.baselineterm.get_follow_up(region=None)

        self.assertEqual(len(dates), 2)  # Two dates 1/1 and 1/2
        self.assertEqual(len(follow_ups), 2)  # Two regions for the follow up dictionary
        # Sum the follow up data for two contacts in Region 1
        self.assertEqual(
            follow_ups[self.region1.name]["values"],
            [24, 18])
        # Data for Region 2 only from one contact
        self.assertEqual(
            follow_ups[self.region2.name]["values"],
            [25, 20])
