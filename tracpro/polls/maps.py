from collections import Counter
from itertools import groupby
from operator import itemgetter

from django.db.models import F

from .models import Answer
from .utils import natural_sort_key


def color_code_categories(categories):
    # dark_green = '#006837'
    # red = '#A7082C'
    # dark_blue = '#1F49BF'
    # orange = '#FF8200'
    # yellow = '#FFD100'
    # light_green = '#94D192'
    # light_red = '#F2A2B3'
    # light_blue = '#96AEF2'
    # light_orange = '#FDC690'
    # light_yellow = '#FFFFBF'

    vivid_colors = ['#006837', '#A7082C', '#1F49BF', '#FF8200', '#FFD100']
    light_colors = ['#94D192', '#F2A2B3', '#96AEF2', '#FDC690', '#FFFFBF']

    if len(categories) > 5:
        # Use full set of colors for > 5 categories
        all_colors = vivid_colors + light_colors
        category_colors = dict(zip(categories, all_colors[:len(categories)]))
    else:
        category_colors = dict(zip(categories, vivid_colors[:len(categories)]))

    return category_colors


def data_categoric(responses, question):
    # Split question answers by boundary.
    # For each region, calculate the most common answer

    answers = Answer.objects.filter(response__in=responses, question=question)
    categories = answers.distinct('category').values_list('category', flat=True)
    categories = [category.encode('ascii') for category in categories]
    categories.sort(key=natural_sort_key)
    category_colors = color_code_categories(categories)

    answers = answers.annotate(boundary=F('response__contact__region__boundary'))
    answers = answers.values('boundary', 'category')
    answers = answers.order_by('boundary')

    # Return the map data with information for category name, color code
    # for each boundary in the map
    map_data = []
    for boundary_id, _answers in groupby(answers, itemgetter('boundary')):
        category_counts = Counter(a['category'] for a in _answers)
        top_category = category_counts.most_common(1)[0][0]
        map_data.append({
            'boundary': boundary_id,
            'color': category_colors[top_category],
            'category': top_category,
        })

    return map_data, category_colors
