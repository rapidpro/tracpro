from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import maps
from .. import models


class BaseMapsTest(TracProTest):

    def setUp(self):
        super(BaseMapsTest, self).setUp()

        self.org = factories.Org()
        self.poll = factories.Poll()

        self.question_numeric = factories.Question(
            poll=self.poll,
            rules=[
                {
                    'category': {'base': '1-5'},
                    'test': {'type': 'between', 'min': '1', 'max': '5'},
                },
                {
                    'category': {'base': '6-10'},
                    'test': {'type': 'between', 'min': '5', 'max': '10'},
                },
                {
                    'category': {'base': '>10'},
                    'test': {'type': 'gt', 'test': '10'},
                },
            ],
        )
        self.question_category = factories.Question(
            poll=self.poll,
            rules=[
                {'category': 'orange', 'test': {}},
                {'category': 'red', 'test': {}},
                {'category': 'purple', 'test': {}})
        self.question_open = factories.Question(poll=self.poll)

        self.boundary = factories.Boundary(org=self.org)

        self.contact_1 = factories.Contact(
            org=self.org,
            region=factories.Region(
                org=self.org,
                boundary=self.boundary))
        self.response_1 = factories.Response(
            pollrun__poll=self.poll, contact=self.contact_1)
        self.answer_1a = factories.Answer(
            response=self.response_1, question=self.question_numeric,
            category="Other", value="-1")
        self.answer_1b = factories.Answer(
            response=self.response_1, question=self.question_category,
            category="purple", value="eggplant")
        self.answer_1c = factories.Answer(
            response=self.response_1, question=self.question_open,
            category=None, value="happy holidays")

        self.contact_2 = factories.Contact(
            org=self.org,
            region=factories.Region(
                org=self.org,
                boundary=None))
        self.response_2 = factories.Response(
            pollrun__poll=self.poll, contact=self.contact_2)
        self.answer_2a = factories.Answer(
            response=self.response_2, question=self.question_numeric,
            category=">5", value="8")
        self.answer_2b = factories.Answer(
            response=self.response_2, question=self.question_category,
            category="red", value="rojo")
        self.answer_2c = factories.Answer(
            response=self.response_2, question=self.question_open,
            category=None, value="violets are blue")

        self.contact_3 = factories.Contact(
            org=self.org,
            region=factories.Region(
                org=self.org,
                boundary=self.boundary))
        self.response_3 = factories.Response(
            pollrun__poll=self.poll, contact=self.contact_3)
        self.answer_3a = factories.Answer(
            response=self.response_3, question=self.question_numeric,
            category="1-5", value="3")
        self.answer_3b = factories.Answer(
            response=self.response_3, question=self.question_category,
            category="red", value="rouge")
        self.answer_3c = factories.Answer(
            response=self.response_3, question=self.question_open,
            category=None, value="roses are red")


class TestGetAnswers(BaseMapsTest):

    def test_get_answers(self):
        """Method should return all answers that are associated with a Boundary."""
        responses = models.Response.objects.all()
        answers = maps.get_answers(responses, self.question_numeric)
        self.assertEqual(len(answers), 2)
        self.assertIn(self.answer_1a, answers)
        self.assertNotIn(self.answer_2a, answers)
        self.assertIn(self.answer_3a, answers)
        self.assertEqual(answers.get(pk=self.answer_1a.pk).boundary, self.boundary.pk)
        self.assertEqual(answers.get(pk=self.answer_3a.pk).boundary, self.boundary.pk)


class TestMapData(BaseMapsTest):

    def test_no_answers(self):
        responses = models.Response.objects.filter(pk=self.response_2.pk)
        data = maps.get_map_data(responses, self.question_numeric)
        self.assertEqual(data, None)

    def test_numeric_map_data(self):
        responses = models.Response.objects.all()
        data = maps.get_map_data(responses, self.question_numeric)
        self.assertEqual(set(data.keys()), set(('map-data', 'all-categories')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary.pk: "1-5",  # (3 + -1) / 2 = 1
        })

    def test_category_map_data(self):
        responses = models.Response.objects.all()
        data = maps.get_map_data(responses, self.question_category)
        self.assertEqual(set(data.keys()), set(('map-data', 'all-categories')))
