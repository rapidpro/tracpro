from __future__ import unicode_literals

from collections import Counter
from itertools import groupby
from operator import itemgetter

import numpy

from django.db.models import F

from tracpro.charts.formatters import format_number

from .utils import get_numeric_values
from . import rules


def get_map_data(responses, question):
    answers = get_answers(responses, question)

    if question.question_type == question.TYPE_NUMERIC:
        map_data = numeric_map_data(answers, question)
    elif question.question_type == question.TYPE_MULTIPLE_CHOICE:
        map_data = multiple_choice_map_data(answers, question)
    else:
        map_data = None

    if map_data:
        return {
            'map-data': map_data,
            'all-categories': rules.get_all_categories(question, answers),
        }
    else:
        return None


def get_answers(responses, question):
    """Return answers to the question from the responses, annotated with `boundary`.

    Excludes answers that are not associated with a boundary.
    """
    answers = question.answers.filter(response__in=responses)
    answers = answers.annotate(boundary=F('response__contact__region__boundary'))
    answers = answers.exclude(boundary=None)
    return answers


def numeric_map_data(answers, question):
    """For each boundary, display the category of the average answer value."""
    map_data = {}
    answer_data = [
        {
            'boundary': answer.boundary,
            'value_to_use': answer.value_to_use
        }
        for answer in answers.order_by('boundary')
    ]

    for boundary_id, _answers in groupby(answer_data, itemgetter('boundary')):
        values = get_numeric_values(a['value_to_use'] for a in _answers)
        if len(values) > 0:
            average = round(numpy.mean(values), 2)
            map_data[boundary_id] = {
                'average': format_number(average, digits=2),
                'category': question.categorize(average),
            }
    return map_data


def multiple_choice_map_data(answers, question):
    """For each boundary, display the most common answer category."""
    map_data = {}
    answer_data = answers.exclude(category=None).exclude(category="")
    answer_data = answer_data.order_by('boundary').values('boundary', 'category')
    for boundary_id, _answers in groupby(answer_data, itemgetter('boundary')):
        top_category = Counter(a['category'] for a in _answers).most_common(1)[0][0]
        map_data[boundary_id] = {
            'category': top_category,
        }
    return map_data
