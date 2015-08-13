from tracpro.test import TracProTest
from ..forms import BaselineTermForm


class TestBaselineTermForm(TracProTest):
    form_class = BaselineTermForm

    def setUp(self):
        super(TestBaselineTermForm, self).setUp()
        self.org = self.unicef
        self.data = {
            'name': 'Test Baseline Term',
            'org': self.org.pk,
            'start_date': '2015-05-01',
            'end_date': '2015-05-10',
            'baseline_poll': self.poll1.pk,
            'baseline_question': self.poll1_question1.pk,
            'follow_up_poll': self.poll1.pk,
            'follow_up_question': self.poll1_question2.pk,
        }

    def test_valid_form(self):
        """This form should pass validation."""
        form = self.form_class(data=self.data)
        self.assertTrue(form.is_valid())