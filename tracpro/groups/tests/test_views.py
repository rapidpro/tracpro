import json

from dateutil.relativedelta import relativedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from tracpro.polls import models as polls
from tracpro.test.cases import TracProDataTest


class TestRegionList(TracProDataTest):
    url_name = "groups.region_list"

    def test_list_non_admin(self):
        self.login(self.user1)  # not an admin
        url = reverse(self.url_name)
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, "unicef", url)

    def test_list_admin(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)


class TestRegionMostActive(TracProDataTest):
    url_name = "groups.region_most_active"

    def test_most_active(self):
        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)

        pollrun = polls.PollRun.objects.create(
            poll=self.poll1,
            conducted_on=five_weeks_ago,
        )

        # empty response in last month for contact in region #1
        polls.Response.objects.create(
            flow_run_id=123, pollrun=pollrun, contact=self.contact1,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_EMPTY)

        # partial response not in last month for contact in region #2
        polls.Response.objects.create(
            flow_run_id=234, pollrun=pollrun, contact=self.contact4,
            created_on=five_weeks_ago, updated_on=five_weeks_ago,
            status=polls.RESPONSE_PARTIAL)

        # partial response in last month for contact in region #2
        polls.Response.objects.create(
            flow_run_id=345, pollrun=pollrun, contact=self.contact4,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_PARTIAL)

        # 2 complete responses in last month for contact in region #3
        polls.Response.objects.create(
            flow_run_id=456, pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_COMPLETE)

        polls.Response.objects.create(
            flow_run_id=567, pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', reverse(self.url_name))
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.region3.pk)
        self.assertEqual(results[0]['name'], self.region3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.region2.pk)
        self.assertEqual(results[1]['name'], self.region2.name)
        self.assertEqual(results[1]['response_count'], 1)


class TestGroupList(TracProDataTest):
    url_name = "groups.group_list"

    def test_non_admin(self):
        self.login(self.user1)  # not an admin
        url = reverse(self.url_name)
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, "unicef", url)

    def test_admin(self):
        self.login(self.admin)
        response = self.url_get('unicef', reverse(self.url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)


class TestGroupMostActive(TracProDataTest):
    url_name = "groups.group_most_active"

    def test_most_active(self):
        five_weeks_ago = timezone.now() - relativedelta(weeks=5)
        five_days_ago = timezone.now() - relativedelta(days=5)
        pollrun = polls.PollRun.objects.create(
            poll=self.poll1,
            conducted_on=five_weeks_ago,
        )

        # empty response in last month for contact in group #1
        polls.Response.objects.create(
            flow_run_id=123, pollrun=pollrun, contact=self.contact1,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_EMPTY)

        # partial response not in last month for contact in group #2
        polls.Response.objects.create(
            flow_run_id=234, pollrun=pollrun, contact=self.contact3,
            created_on=five_weeks_ago, updated_on=five_weeks_ago,
            status=polls.RESPONSE_PARTIAL)

        # partial response in last month for contact in group #2
        polls.Response.objects.create(
            flow_run_id=345, pollrun=pollrun, contact=self.contact3,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_PARTIAL)

        # 2 complete responses in last month for contact in group #3
        polls.Response.objects.create(
            flow_run_id=456, pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_COMPLETE)

        polls.Response.objects.create(
            flow_run_id=567, pollrun=pollrun, contact=self.contact5,
            created_on=five_days_ago, updated_on=five_days_ago,
            status=polls.RESPONSE_COMPLETE)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', reverse(self.url_name))
        results = json.loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], self.group3.pk)
        self.assertEqual(results[0]['name'], self.group3.name)
        self.assertEqual(results[0]['response_count'], 2)
        self.assertEqual(results[1]['id'], self.group2.pk)
        self.assertEqual(results[1]['name'], self.group2.name)
        self.assertEqual(results[1]['response_count'], 1)
