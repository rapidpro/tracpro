from django.db.models import Count, F

from .models import Answer


def color_code_categories(categories):
    # dark_green = '#006837'
    # yellow = '#FFD100'
    # dark_blue = '#1F49BF'
    # red = '#A7082C'
    # orange = '#FF8200'
    # light_green = '#94D192'
    # light_blue = '#96AEF2'
    # light_red = '#F2A2B3'
    # light_orange = '#FDC690'
    # light_yellow = '#FFFFBF'

    vivid_colors = ['#006837', '#FFD100', '#1F49BF', '#A7082C', '#FF8200']
    light_colors = ['#94D192', '#96AEF2', '#F2A2B3', '#FDC690', '#FFFFBF']

    categories = [''.join(category).encode('ascii') for category in categories]
    if len(categories) > 5:
        all_colors = vivid_colors + light_colors
        category_colors = dict(zip(categories, all_colors[:len(categories)]))
    else:
        category_colors = dict(zip(categories, vivid_colors[:len(categories)]))

    return category_colors


def data_categoric(responses, question):
    # Split question answers by boundary.
    # For each region, calculate the most common answer

    answers = Answer.objects.filter(response__in=responses, question=question)
    categories = answers.distinct('category').values_list('category')
    category_colors = color_code_categories(categories)

    answers = answers.annotate(boundary=F(
        'response__contact__region__boundary')).values('boundary', 'category')
    answers = answers.order_by('boundary')
    answers = answers.annotate(category_count=Count('category'))

    map_data = []
    boundary = ''
    category = ''
    category_count = 0
    for answer in answers:
        if boundary and boundary != answer['boundary']:
            # Append the category with most results for boundary
            map_data.append(
                {'category': category,
                 'boundary': boundary})
            category_count = 0
            category = ''
        boundary = answer['boundary']
        if answer['category_count'] > category_count:
            category_count = answer['category_count']
            category = answer['category']
    # Append last data point
    map_data.append(
        {'category': category,
         'boundary': boundary})

    return map_data, category_colors
