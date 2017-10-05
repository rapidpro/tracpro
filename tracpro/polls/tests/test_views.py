# coding=utf-8
from __future__ import absolute_import, unicode_literals

import csv
import datetime
from StringIO import StringIO

import pytz

from django.core.urlresolvers import reverse

from tracpro.test.cases import TracProDataTest

from ..models import Response
from . import factories


class PollCRUDLTest(TracProDataTest):

    def test_list(self):
        url = reverse('polls.poll_list')

        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_read(self):
        url = reverse('polls.poll_read', kwargs={'pk': self.poll1.pk})
        # log in as admin
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].pk, self.poll1.pk)
        self.assertEqual(self.poll1.name, response.context['title'])
        self.assertEqual(2, len(response.context['question_data']))


class ResponseCRUDLTest(TracProDataTest):

    def setUp(self):
        super(ResponseCRUDLTest, self).setUp()
        date1 = datetime.datetime(2014, 1, 1, 7, tzinfo=pytz.UTC)
        date2 = datetime.datetime(2014, 1, 1, 8, tzinfo=pytz.UTC)
        date3 = datetime.datetime(2014, 1, 2, 7, tzinfo=pytz.UTC)

        self.mock_temba_client.create_flow_start.return_value = []

        # create non-regional pollrun with 3 responses (1 complete, 1 partial, 1 empty)
        self.pollrun1 = factories.UniversalPollRun(
            poll=self.poll1, conducted_on=date1)

        self.pollrun1_r1 = factories.Response(
            pollrun=self.pollrun1, contact=self.contact1,
            created_on=date1, updated_on=date1,
            status=Response.STATUS_COMPLETE)
        factories.Answer(
            response=self.pollrun1_r1, question=self.poll1_question1,
            value="5.0000", category="1 - 10", submitted_on=date1)
        factories.Answer(
            response=self.pollrun1_r1, question=self.poll1_question2,
            value="Sunny", category="All Responses", submitted_on=date1)

        self.pollrun1_r2 = factories.Response(
            pollrun=self.pollrun1, contact=self.contact2,
            created_on=date2, updated_on=date2,
            status=Response.STATUS_PARTIAL)
        factories.Answer(
            response=self.pollrun1_r2, question=self.poll1_question1,
            value="6.0000", category="1 - 10", submitted_on=date2)

        self.pollrun1_r3 = factories.Response(
            pollrun=self.pollrun1, contact=self.contact4,
            created_on=date3, updated_on=date3,
            status=Response.STATUS_EMPTY)

        # create regional pollrun with 1 incomplete response
        self.pollrun2 = factories.RegionalPollRun(
            poll=self.poll1, region=self.region1, conducted_on=date3)
        self.pollrun2_r1 = factories.Response(
            pollrun=self.pollrun2, contact=self.contact1,
            created_on=date3, updated_on=date3,
            status=Response.STATUS_PARTIAL)

    def test_by_pollrun(self):
        url = reverse('polls.response_by_pollrun', args=[self.pollrun1.pk])

        # log in as admin
        self.login(self.admin)

        # view responses for pollrun #1
        response = self.url_get('unicef', url)
        self.assertContains(response, "Number of sheep", status_code=200)
        self.assertContains(response, "How is the weather?")

        responses = list(response.context['object_list'])
        self.assertEqual(len(responses), 2)
        # newest non-empty first
        self.assertEqual(responses, [self.pollrun1_r2, self.pollrun1_r1])

        # can't restart from "All Regions" view of responses
        self.assertFalse(response.context['can_restart'])

        self.switch_region(self.region1)

        # can't restart as there is a later pollrun of the same poll in region #1
        response = self.url_get('unicef', url)
        self.assertFalse(response.context['can_restart'])

        self.switch_region(self.region2)

        # can restart as this is the latest pollrun of this poll in region #2
        response = self.url_get('unicef', url)
        self.assertTrue(response.context['can_restart'])

    def test_by_contact(self):
        # log in as admin
        self.login(self.admin)

        # view responses for contact #1
        url = reverse('polls.response_by_contact', args=[self.contact1.pk])
        response = self.url_get('unicef', url)

        responses = list(response.context['object_list'])
        self.assertEqual(len(responses), 2)
        # newest non-empty first
        self.assertEqual(responses, [self.pollrun2_r1, self.pollrun1_r1])

    def test_fetching_pollruns_csv(self):
        # log in as admin
        self.login(self.admin)

        url = reverse('polls.response_by_pollrun', args=[self.pollrun1.pk]) + "?_format=csv"
        response = self.url_get('unicef', url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/csv', response['Content-Type'])

        rows = [row for row in csv.reader(StringIO(response.content.decode('utf-8')))]
        self.assertEqual(rows[0], ['Date', 'Name', 'URN', 'Panel', 'Cohort', 'Number of sheep', 'How is the weather?'])
        self.assertEqual(rows[1], [
                                    'Jan 01, 2014 12:30',
                                    'Bob',
                                    'tel:2345',
                                    'Kandahar',
                                    'Farmers, Kandahar',
                                    '6.0000',
                                    '',
                                ])
        self.assertEqual(rows[2], [
                                    'Jan 01, 2014 11:30',
                                    'Ann',
                                    'tel:1234',
                                    'Kandahar',
                                    'Farmers, Teachers',
                                    '5.0000',
                                    'Sunny',
                                ])
        self.assertEqual(3, len(rows))
