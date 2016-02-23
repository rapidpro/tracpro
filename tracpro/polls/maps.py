from collections import Counter
from itertools import groupby
from operator import itemgetter

from django.db.models import F

from .utils import natural_sort_key


def get_map_data(responses, question):
    answers = question.answers.filter(response__in=responses)

    all_categories = answers.distinct('category').values_list('category', flat=True)
    all_categories = [c.encode('ascii') for c in all_categories]
    all_categories.sort(key=natural_sort_key)

    map_data = categorical_map_data(answers)

    return {
        'map-data': map_data,
        'all-categories': all_categories,
    }


def categorical_map_data(answers):
    """Display the most common Answer category per Boundary."""
    answers = answers.annotate(boundary=F('response__contact__region__boundary'))
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
