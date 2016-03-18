from __future__ import unicode_literals

from tracpro.test import factories
from tracpro.test.cases import TracProTest

from .. import maps
from .. import models


class BaseMapsTest(TracProTest):

    def setUp(self):
        """Set up common resources."""
        super(BaseMapsTest, self).setUp()

        self.org = factories.Org()
        self.poll = factories.Poll()
        self.pollrun = factories.PollRun(poll=self.poll)

        # Sometimes multiple regions share a Boundary.
        self.boundary_a = factories.Boundary(org=self.org)
        self.region_a1 = factories.Region(org=self.org, boundary=self.boundary_a)
        self.region_a2 = factories.Region(org=self.org, boundary=self.boundary_a)

        # Sometimes only one region uses a particular Boundary.
        self.boundary_b = factories.Boundary(org=self.org)
        self.region_b = factories.Region(org=self.org, boundary=self.boundary_b)

        # Sometimes regions are not associated with a Boundary.
        self.region_no_boundary = factories.Region(org=self.org, boundary=None)

        # Create empty responses for several scenarios.
        self.response_for_a1 = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_a1))
        self.response_for_a2 = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_a2))
        self.response1_for_b = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_b))
        self.response2_for_b = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_b))  # repeated region.
        self.response_for_no_boundary = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_no_boundary))


class TestGetAnswers(BaseMapsTest):

    def setUp(self):
        super(TestGetAnswers, self).setUp()
        self.question = factories.Question(poll=self.poll)

    def test_get_answers(self):
        """Function should return all Answers that are associated with a Boundary."""
        answer1 = factories.Answer(
            response=self.response_for_a1, question=self.question)
        answer2 = factories.Answer(
            response=self.response_for_a2, question=self.question)
        answer3 = factories.Answer(
            response=self.response1_for_b, question=self.question)
        answer4 = factories.Answer(
            response=self.response2_for_b, question=self.question)
        factories.Answer(  # not in results because it has no boundary
            response=self.response_for_no_boundary, question=self.question)

        other_question = factories.Question(poll=self.poll)
        factories.Answer(  # not in results because it is for another question
            response=self.response_for_a1, question=other_question)

        answers = maps.get_answers(self.pollrun.responses.all(), self.question)
        self.assertEqual(len(answers), 4)
        self.assertIn(answer1, answers)
        self.assertIn(answer2, answers)
        self.assertIn(answer3, answers)
        self.assertIn(answer4, answers)

        # Each answer should have the boundary annotated.
        self.assertEqual(
            answers.get(pk=answer1.pk).boundary, self.boundary_a.pk)
        self.assertEqual(
            answers.get(pk=answer2.pk).boundary, self.boundary_a.pk)
        self.assertEqual(
            answers.get(pk=answer3.pk).boundary, self.boundary_b.pk)
        self.assertEqual(
            answers.get(pk=answer4.pk).boundary, self.boundary_b.pk)

    def test_get_answer__response_no_boundary(self):
        """Function should return no answers if the responses have no associated Boundaries."""
        # Ensure that a related answer exists.
        factories.Answer(
            response=self.response_for_no_boundary, question=self.question)

        responses = models.Response.objects.filter(pk=self.response_for_no_boundary.pk)
        answers = maps.get_answers(responses, self.question)
        self.assertEqual(len(answers), 0)


class TestNumericMapData(BaseMapsTest):

    def setUp(self):
        super(TestNumericMapData, self).setUp()
        self.question = factories.Question(
            poll=self.poll,
            question_type=models.Question.TYPE_NUMERIC,
            rules=[
                {
                    'category': {'base': '1-5'},
                    'test': {'type': 'between', 'min': '1', 'max': '5'},
                },
                {
                    'category': {'base': '>5'},
                    'test': {'type': 'gt', 'test': '5'},
                },
            ])

    def test_numeric__no_responses(self):
        """Returns None if an empty response queryset is passed."""
        # Ensure one relevant answer exists.
        factories.Answer(
            response=self.response_for_a1, question=self.question)

        responses = models.Response.objects.none()
        data = maps.get_map_data(responses, self.question)
        self.assertEqual(data, None)

    def test_numeric__no_boundaries(self):
        """Responses not associated with a boundary should be filtered out."""
        factories.Answer(
            response=self.response_for_no_boundary, question=self.question)

        responses = models.Response.objects.filter(pk=self.response_for_no_boundary.pk)
        data = maps.get_map_data(responses, self.question)
        self.assertEqual(data, None)

    def test_numeric__multiple_regions_per_boundary(self):
        """Responses should be grouped by Boundary rather than region."""
        # Both region_a1 and region_a2 point to boundary_a.
        factories.Answer(
            category="1-5", value="3",
            response=self.response_for_a1, question=self.question)
        factories.Answer(
            category=">5", value="11",
            response=self.response_for_a2, question=self.question)

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': 7,  # (3 + 11) / 2
                'category': '>5',
            },
        })

    def test_numeric__multiple_answers_per_region(self):
        """Multiple answers per region are averaged."""
        # Create two answers for region_b.
        factories.Answer(
            category="1-5", value="3",
            response=self.response1_for_b, question=self.question)
        factories.Answer(
            category=">5", value="11",
            response=self.response2_for_b, question=self.question)

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_b.pk: {
                'average': 7,  # (3 + 11) / 2
                'category': '>5',
            },
        })

    def test_numeric__other_category(self):
        """Categorize average as "Other" if no rule matches."""
        factories.Answer(
            category="1-5", value="3",
            response=self.response1_for_b, question=self.question)
        factories.Answer(
            category="", value="-5",
            response=self.response2_for_b, question=self.question)

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_b.pk: {
                'average': -1,  # (3 + -5) / 2
                'category': 'Other',
            },
        })

    def test_numeric(self):
        """Test expected response with a full slate of answers."""
        factories.Answer(
            category="1-5", value="2",
            response=self.response_for_a1, question=self.question)
        factories.Answer(
            category=">5", value="6",
            response=self.response_for_a2, question=self.question)
        factories.Answer(
            category="1-5", value="4",
            response=self.response1_for_b, question=self.question)
        factories.Answer(
            category="foo", value="8",  # previously unknown category
            response=self.response2_for_b, question=self.question)
        factories.Answer(
            category=">5", value="6",
            response=self.response_for_no_boundary, question=self.question)

        # Data from another question is ignored.
        other_question = factories.Question(poll=self.poll)
        other_response = factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=self.region_a1))
        factories.Answer(
            category="zero", value="0",
            response=other_response, question=other_question)

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'foo', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': 4,  # (2 + 6) / 2
                'category': '1-5',
            },
            self.boundary_b.pk: {
                'average': 6,  # (4 + 8) / 2
                'category': '>5',
            },
        })


class TestCategoryMapData(BaseMapsTest):

    def setUp(self):
        super(TestCategoryMapData, self).setUp()
        self.question = factories.Question(
            poll=self.poll,
            question_type=models.Question.TYPE_MULTIPLE_CHOICE,
            rules=[
                {'category': 'orange', 'test': {}},
                {'category': 'red', 'test': {}},
                {'category': 'purple', 'test': {}},
            ])


class TestOpenEndedMapData(BaseMapsTest):

    def setUp(self):
        super(TestOpenEndedMapData, self).setUp()
        self.question = factories.Question(
            poll=self.poll,
            question_type=models.Question.TYPE_OPEN,
            rules=[])
