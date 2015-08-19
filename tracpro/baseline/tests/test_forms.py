from django.core.exceptions import NON_FIELD_ERRORS

from tracpro.test.cases import TracProDataTest
from ..forms import BaselineTermForm


class TestBaselineTermForm(TracProDataTest):
    form_class = BaselineTermForm

    def setUp(self):
        super(TestBaselineTermForm, self).setUp()

        self.org = self.unicef
        self.data = {
            'name': 'Test Baseline Term',
            'org': self.org.pk,
            'region': self.region1.pk,
            'start_date': '2015-05-01',
            'end_date': '2015-05-10',
            'baseline_poll': self.poll1.pk,
            'baseline_question': self.poll1_question1.pk,
            'follow_up_poll': self.poll1.pk,
            'follow_up_question': self.poll1_question2.pk,
        }

    def test_valid_form(self):
        """This form should pass validation."""
        form = self.form_class(data=self.data, user=self.admin)
        self.assertTrue(form.is_valid())

    def test_missing_field(self):
        """No region selected, should be invalid."""
        self.data.pop("region")
        form = self.form_class(data=self.data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertEqual(form.errors['region'],
                         ['This field is required.'])

    def test_bad_dates(self):
        """Start date after end date should be invalid."""
        self.data["start_date"] = '2015-05-01'
        self.data["end_date"] = '2015-01-01'
        form = self.form_class(data=self.data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertTrue(NON_FIELD_ERRORS in form.errors, form.errors)
        self.assertEqual(form.errors[NON_FIELD_ERRORS],
                         ['Start date should be before end date.'],
                         form.errors)

    def test_same_question(self):
        """Baseline question and follow up question should be different, form is invalid."""
        self.data["baseline_question"] = self.poll1_question1.pk
        self.data["follow_up_question"] = self.poll1_question1.pk
        form = self.form_class(data=self.data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1, form.errors)
        self.assertTrue(NON_FIELD_ERRORS in form.errors, form.errors)
        self.assertEqual(form.errors[NON_FIELD_ERRORS],
                         ['Baseline question and follow up question should be different.'],
                         form.errors)
