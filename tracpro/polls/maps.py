from collections import Counter
from itertools import groupby
from operator import itemgetter

import numpy

from django.db.models import F

from .utils import get_numeric_values
from . import rules


def get_map_data(responses, question):
    answers = question.answers.filter(response__in=responses)
    answers = answers.annotate(boundary=F('response__contact__region__boundary'))
    answers = answers.order_by('boundary')

    if question.question_type == question.TYPE_NUMERIC:
        map_data = numeric_map_data(answers, question)
    else:
        map_data = categorical_map_data(answers, question)

    return {
        'map-data': map_data,
        'all-categories': rules.get_all_categories(question),
    }


def numeric_map_data(answers, question):
    """For each boundary, display the category of the average answer value."""
    map_data = {}
    answer_data = answers.values('boundary', 'value')
    for boundary_id, _answers in groupby(answer_data, itemgetter('boundary')):
        average = numpy.mean(get_numeric_values(a['value'] for a in _answers))
        map_data[boundary_id] = question.categorize(average)
    return map_data


def categorical_map_data(answers, question):
    """For each boundary, display the most common answer category."""
    map_data = {}
    answer_data = answers.values('boundary', 'category')
    for boundary_id, _answers in groupby(answer_data, itemgetter('boundary')):
        category_counts = Counter(a['category'] for a in _answers)
        top_category = category_counts.most_common(1)[0][0]
        map_data[boundary_id] = top_category
    return map_data
