from __future__ import unicode_literals

import datetime

from django.core.urlresolvers import reverse

from tracpro.polls.models import Answer, PollRun, Response
from tracpro.test.cases import TracProDataTest

from ..models import BaselineTerm


class TestBaselineTermCRUDL(TracProDataTest):

    def setUp(self):
        """
         There will be a set of results for 3 contacts, in 2 regions
          self.contact1 and self.contact2 are in self.region1
          self.contact4 is in self.region2
        """
        super(TestBaselineTermCRUDL, self).setUp()

        self.org = self.unicef
        self.baselineterm = BaselineTerm.objects.create(
            name='Baseline Term SetUp',
            org=self.org,
            start_date=datetime.date(2015, 5, 1),
            end_date=datetime.date(2015, 5, 1),
            baseline_poll=self.poll1,
            baseline_question=self.poll1_question1,
            follow_up_poll=self.poll1,
            follow_up_question=self.poll1_question2
        )

        self.data = {
            'name': 'Test Baseline Term',
            'org': self.org.pk,
            'start_date': 'May 1, 2015',
            'end_date': 'May 1, 2015',
            'baseline_poll': self.poll1.pk,
            'baseline_question': self.poll1_question1.pk,
            'follow_up_poll': self.poll1.pk,
            'follow_up_question': self.poll1_question2.pk,
        }

    def test_list(self):
        url_name = "baseline.baselineterm_list"
        self.login(self.admin)
        response = self.url_get('unicef', reverse(url_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_create(self):
        url = reverse('baseline.baselineterm_create')
        # Log in as an org administrator
        self.login(self.admin)
        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # Submit with no fields entered
        response = self.url_post('unicef', url, {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'name', 'This field is required.')

        # Submit with form data
        response = self.url_post('unicef', url, self.data)
        self.assertEqual(response.status_code, 302)

        # Check new BaselineTerm created successfully
        baselineterm = BaselineTerm.objects.all().last()
        self.assertEqual(baselineterm.name, "Test Baseline Term")

    def test_delete(self):
        # Log in as an org administrator
        self.login(self.admin)

        # Delete baselineterm from setUp()
        response = self.url_post(
            'unicef', reverse('baseline.baselineterm_delete', args=[self.baselineterm.pk]))

        # This should delete the single BaselineTerm and redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 'http://unicef.testserver/indicators/', fetch_redirect_response=False)
        self.assertEqual(BaselineTerm.objects.all().count(), 0)

    def test_update(self):
        # Log in as an org administrator
        self.login(self.admin)
        url = reverse('baseline.baselineterm_update', args=[self.baselineterm.pk])

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        self.data["name"] = "Baseline Term Updated"
        response = self.url_post('unicef', url, self.data)
        self.assertEqual(response.status_code, 302)

        # Check updated BaselineTerm
        baselineterm_updated = BaselineTerm.objects.get(pk=self.baselineterm.pk)
        self.assertRedirects(
            response,
            'http://unicef.testserver/indicators/read/%d/' % self.baselineterm.pk,
            fetch_redirect_response=False)
        self.assertEqual(baselineterm_updated.name, "Baseline Term Updated")

    def test_read(self):
        # Log in as an org administrator
        self.login(self.admin)

        # Try to read the one BaselineTerm
        response = self.url_get(
            'unicef', reverse('baseline.baselineterm_read', args=[self.baselineterm.pk]))
        self.assertEqual(response.status_code, 200)

        # Try to view BaselineTerm that does not exist
        fake_baselineterm_pk = self.baselineterm.pk + 100
        response = self.url_get(
            'unicef', reverse('baseline.baselineterm_read', args=[fake_baselineterm_pk]))
        self.assertEqual(response.status_code, 404)

    def test_data_spoof(self):
        # Turn on show_spoof_data for this org
        self.org.show_spoof_data = True
        self.org.save()
        url = reverse('baseline.baselineterm_data_spoof')
        # Log in as an org administrator
        self.login(self.admin)
        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # Submit with no fields entered
        response = self.url_post('unicef', url, {})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'contacts', 'This field is required.')

        spoof_data = {
            'contacts': [self.contact1.pk],
            'start_date': "May 1, 2015",
            'end_date': "May 2, 2015",
            'baseline_question': self.poll1_question1.pk,
            'follow_up_question': self.poll1_question2.pk,
            'baseline_minimum': 30,
            'baseline_maximum': 40,
            'follow_up_minimum': 10,
            'follow_up_maximum': 20
        }

        # Submit with  valid form data
        response = self.url_post('unicef', url, spoof_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            'http://unicef.testserver/indicators/',
            fetch_redirect_response=False)

        # Check new spoofed data created successfully
        # 3 PollRuns, Responses, and Answers
        # for 1 Baseline Date and 2 Follow Up Dates
        self.assertEqual(PollRun.objects.all().count(), 3)
        self.assertEqual(Response.objects.all().count(), 3)
        self.assertEqual(Answer.objects.all().count(), 3)

    def test_data_spoof_hide(self):
        # Turn off show_spoof_data for this org
        self.org.show_spoof_data = False
        self.org.save()
        url = reverse('baseline.baselineterm_data_spoof')
        # Log in as an org administrator
        self.login(self.admin)
        response = self.url_get('unicef', url)
        # We should not be able to spoof data
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            'http://unicef.testserver/indicators/',
            fetch_redirect_response=False)
