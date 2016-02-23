from collections import Counter
from itertools import groupby
from operator import itemgetter

import numpy

from django.db.models import F

from . import utils


def get_map_data(responses, question):
    answers = question.answers.filter(response__in=responses)
    answers = answers.annotate(boundary=F('response__contact__region__boundary'))

    all_categories = list(answers.distinct('category').values_list('category', flat=True))
    all_categories.sort(key=utils.natural_sort_key)

    if question.question_type == question.TYPE_NUMERIC:
        map_data = numeric_map_data(answers, question)
    else:
        map_data = categorical_map_data(answers, question)

    return {
        'map-data': map_data,
        'all-categories': all_categories,
    }


def numeric_map_data(answers, question):
    """Display the category of the average numeric Answer value per Boundary."""
    answers = answers.order_by('boundary').values('boundary', 'value')

    map_data = []
    for boundary_id, _answers in groupby(answers, itemgetter('boundary')):
        numeric_values = utils.get_numeric_values(a['value'] for a in _answers)
        average = numpy.mean(numeric_values)
        category = question.categorize(average)
        map_data.append({
            'boundary': boundary_id,
            'category': category,
        })

    return map_data


def categorical_map_data(answers, question):
    """Display the most common Answer category per Boundary."""
    answers = answers.order_by('boundary').values('boundary', 'category')

    map_data = []
    for boundary_id, _answers in groupby(answers, itemgetter('boundary')):
        category_counts = Counter(a['category'] for a in _answers)
        top_category = category_counts.most_common(1)[0][0]
        map_data.append({
            'boundary': boundary_id,
            'category': top_category,
        })

    return map_data
