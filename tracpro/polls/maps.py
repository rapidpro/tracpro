from django.db.models import Count, F

from .models import Answer


def data_categoric(responses, question):
    # Split question answers by boundary.
    # For each region, calculate the most common answer

    answers = Answer.objects.filter(response__in=responses, question=question)
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

    return map_data
