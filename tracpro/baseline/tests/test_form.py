from tracpro.test import TracProTest
from ..forms import BaselineTermForm


class UserFormTests(TracProTest):
    form_class = BaselineTermForm

    def setUp(self):
        super(UserFormTests, self).setUp()
        self.org = self.unicef
        self.data = {
            'name': 'Test Baseline Term',
            'org': self.org,
            'start_date': '2015-05-01',
            'end_date': '2015-05-10',
            'baseline_poll': self.poll1.pk,
            'baseline_question': self.poll1_question1.pk,
            'follow_up_poll': self.poll1.pk,
            'follow_up_question': self.poll1_question2.pk,
        }

    def test_valid_form(self):
        """This form should pass validation."""

        form = self.form_class(data=self.data) #, instance=self.org
        import ipdb; ipdb.set_trace();
        self.assertTrue(form.is_valid())
        #self.assertEqual(len(form.errors), 1, form.errors)
        #self.assertTrue('available_languages' in form.errors, form.errors)
        #self.assertEqual(form.errors['available_languages'],
        #                 ['This field is required.'])
