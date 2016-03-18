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

        self.boundary_a = factories.Boundary(org=self.org)
        self.boundary_b = factories.Boundary(org=self.org)

    def _create_answer(self, question=None, **kwargs):
        """Wrapper to create an Answer with common default values."""
        # If user did not specify response, generate one.
        response = kwargs.pop('response', None)
        region = kwargs.pop('region', None)
        boundary = kwargs.pop('boundary', None)
        if response:
            if region or boundary:
                raise Exception("Cannot specify region or boundary with response.")
        else:
            if region and boundary:
                raise Exception("Please specify either region or boundary, but not both. ")
            region = region or self._create_region(boundary)
            response = self._create_response(region)

        return factories.Answer(
            question=question or self.question, response=response, **kwargs)

    def _create_region(self, boundary):
        """Wrapper to create a region for the boundary."""
        return factories.Region(org=self.org, boundary=boundary)

    def _create_response(self, region):
        """Wrapper to create a response for the region."""
        return factories.Response(
            pollrun=self.pollrun,
            contact=factories.Contact(org=self.org, region=region))


class TestGetAnswers(BaseMapsTest):

    def setUp(self):
        super(TestGetAnswers, self).setUp()
        self.question = factories.Question(poll=self.poll)

    def test_get_answers(self):
        """Function should return all Answers that are associated with a Boundary."""
        region_a1 = self._create_region(self.boundary_a)
        region_a2 = self._create_region(self.boundary_a)
        region_b = self._create_region(self.boundary_b)

        answer1 = self._create_answer(region=region_a1)
        answer2 = self._create_answer(region=region_a2)
        answer3 = self._create_answer(region=region_b)
        answer4 = self._create_answer(region=region_b)
        self._create_answer(boundary=None)  # not in results - no boundary
        self._create_answer(  # not in results - for another question
            question=factories.Question(poll=self.poll),
            response=answer1.response)

        answers = maps.get_answers(self.pollrun.responses.all(), self.question)
        self.assertEqual(len(answers), 4, answers)
        self.assertIn(answer1, answers)
        self.assertIn(answer2, answers)
        self.assertIn(answer3, answers)
        self.assertIn(answer4, answers)

        # Each answer should have the boundary annotated.
        self.assertEqual(answers.get(pk=answer1.pk).boundary, self.boundary_a.pk)
        self.assertEqual(answers.get(pk=answer2.pk).boundary, self.boundary_a.pk)
        self.assertEqual(answers.get(pk=answer3.pk).boundary, self.boundary_b.pk)
        self.assertEqual(answers.get(pk=answer4.pk).boundary, self.boundary_b.pk)

    def test_get_answer__response_no_boundary(self):
        """Return no answers if the responses have no associated Boundaries."""
        # Ensure that a related answer exists.
        self._create_answer(boundary=None)
        answers = maps.get_answers(self.pollrun.responses.all(), self.question)
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
        # Ensure that a relevant answer exists.
        self._create_answer(boundary=self.boundary_a)
        data = maps.get_map_data(self.pollrun.responses.none(), self.question)
        self.assertEqual(data, None)

    def test_numeric__no_boundaries(self):
        """Responses not associated with a boundary should be filtered out."""
        self._create_answer(boundary=None)
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(data, None)

    def test_numeric__multiple_regions_per_boundary(self):
        """Responses should be grouped by Boundary rather than region."""
        self._create_answer(boundary=self.boundary_a, category="1-5", value="3")
        self._create_answer(boundary=self.boundary_a, category=">5", value="11")
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': '7.00',  # (3 + 11) / 2
                'category': '>5',
            },
        })

    def test_numeric__multiple_answers_per_region(self):
        """Multiple answers per region are averaged."""
        region = self._create_region(self.boundary_a)
        self._create_answer(region=region, category="1-5", value="3")
        self._create_answer(region=region, category=">5", value="11")
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': '7.00',  # (3 + 11) / 2
                'category': '>5',
            },
        })

    def test_numeric__other_category(self):
        """Categorize average as "Other" if no rule matches."""
        self._create_answer(boundary=self.boundary_a, category="1-5", value="3")
        self._create_answer(boundary=self.boundary_a, category="", value="-5")
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': '-1.00',  # (3 + -5) / 2
                'category': 'Other',
            },
        })

    def test_numeric__non_numeric_ignored(self):
        """Non-numeric answers should be silently ignored."""
        self._create_answer(boundary=self.boundary_a, category="1-5", value="3")
        self._create_answer(boundary=self.boundary_a, category="1-5", value="invalid")
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': '3.00',
                'category': '1-5',
            },
        })

    def test_numeric(self):
        """Test expected response with a full slate of answers."""
        region_a1 = self._create_region(self.boundary_a)
        region_a2 = self._create_region(self.boundary_a)
        region_b = self._create_region(self.boundary_b)

        self._create_answer(region=region_a1, category="1-5", value="2")
        self._create_answer(region=region_a2, category=">5", value="6")
        self._create_answer(region=region_b, category="1-5", value="4")
        self._create_answer(region=region_b, category="foo", value="8")
        self._create_answer(  # ignored - no boundary
            boundary=None, category=">5", value="6")
        self._create_answer(  # ignored - from another question
            question=factories.Question(poll=self.poll),
            region=region_a1, category="zero", value="0")

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['1-5', '>5', 'foo', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'average': '4.00',  # (2 + 6) / 2
                'category': '1-5',
            },
            self.boundary_b.pk: {
                'average': '6.00',  # (4 + 8) / 2
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
                {'category': 'orange'},
                {'category': 'red'},
                {'category': 'purple'},
            ])

    def test_multiple_choice__no_responses(self):
        """Returns None if an empty response queryset is passed."""
        # Ensure that a relevant answer exists.
        self._create_answer(boundary=self.boundary_a, category='orange')
        data = maps.get_map_data(self.pollrun.responses.none(), self.question)
        self.assertEqual(data, None)

    def test_multiple_choice__no_boundaries(self):
        """Responses not associated with a boundary should be filtered out."""
        self._create_answer(boundary=None, category='orange')
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(data, None)

    def test_multiple_choice__no_category(self):
        """Answers with a null or blank category should be ignored."""
        self._create_answer(boundary=self.boundary_a, category='')
        self._create_answer(boundary=self.boundary_a, category=None)
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(data, None)

    def test_multiple_choice__disregard_no_category(self):
        """Answers with a null or blank category should be ignored."""
        self._create_answer(boundary=self.boundary_a, category='red')
        self._create_answer(boundary=self.boundary_a, category='')
        self._create_answer(boundary=self.boundary_a, category='')
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['orange', 'red', 'purple', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'category': 'red',
            },
        })

    def test_multiple_choice__multiple_regions_per_boundary(self):
        """Responses should be grouped by Boundary rather than region."""
        self._create_answer(boundary=self.boundary_a, category='orange')
        self._create_answer(boundary=self.boundary_a, category='orange')
        self._create_answer(boundary=self.boundary_a, category='red')
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['orange', 'red', 'purple', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'category': 'orange',
            },
        })

    def test_multiple_choice__multiple_answers_per_region(self):
        """Responses should be grouped by Boundary rather than region."""
        region = self._create_region(self.boundary_a)
        self._create_answer(region=region, category='orange')
        self._create_answer(region=region, category='red')
        self._create_answer(region=region, category='red')
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['orange', 'red', 'purple', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'category': 'red',
            },
        })

    def test_multiple_choice__other_category(self):
        """Return most common result even if it is from an unknown category."""
        self._create_answer(boundary=self.boundary_a, category='red')
        self._create_answer(boundary=self.boundary_a, category='foo')
        self._create_answer(boundary=self.boundary_a, category='foo')
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['orange', 'red', 'purple', 'foo', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'category': 'foo',
            },
        })

    def test_multiple_choice(self):
        """Test expected response with a full slate of answers."""
        region_a1 = self._create_region(self.boundary_a)
        region_a2 = self._create_region(self.boundary_a)
        region_b = self._create_region(self.boundary_b)

        self._create_answer(region=region_a1, category="red")
        self._create_answer(region=region_a2, category="red")
        self._create_answer(region=region_b, category="red")
        self._create_answer(region=region_b, category="orange")
        self._create_answer(region=region_b, category="foo")
        self._create_answer(region=region_b, category="foo")
        self._create_answer(  # ignored - no boundary
            boundary=None, category="foo2")
        self._create_answer(  # ignored - from another question
            question=factories.Question(poll=self.poll),
            region=region_a1, category="bar")

        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertEqual(set(data), set(('all-categories', 'map-data')))
        self.assertEqual(data['all-categories'], ['orange', 'red', 'purple', 'foo', 'Other'])
        self.assertEqual(data['map-data'], {
            self.boundary_a.pk: {
                'category': 'red',
            },
            self.boundary_b.pk: {
                'category': 'foo',
            },
        })


class TestOpenEndedMapData(BaseMapsTest):

    def setUp(self):
        super(TestOpenEndedMapData, self).setUp()
        self.question = factories.Question(
            poll=self.poll,
            question_type=models.Question.TYPE_OPEN,
            rules=[])

    def test_not_supported(self):
        """Map data is only supported for numeric and multiple choice questions."""
        # Ensure that a relevant answer exists.
        self._create_answer(boundary=self.boundary_a)
        data = maps.get_map_data(self.pollrun.responses.all(), self.question)
        self.assertIsNone(data)
