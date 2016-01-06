from __future__ import absolute_import, unicode_literals

import cgi
from collections import defaultdict, OrderedDict
import datetime
from decimal import Decimal
from itertools import groupby
import json
import numpy
from operator import itemgetter

from dash.utils import datetime_to_ms

from django.db.models import Count, F
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from .models import Answer, Question, Response


class ChartJsonEncoder(json.JSONEncoder):
    """Encode millisecond timestamps & Decimal objects as floats."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ms(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def single_pollrun(pollrun, question, regions):
    """Chart data for a single pollrun.

    Will be a word cloud for open-ended questions, and pie chart of categories
    for everything else.
    """
    if question.question_type == Question.TYPE_OPEN:
        word_counts = pollrun.get_answer_word_counts(question, regions)
        chart_type = 'word'
        chart_data = word_cloud_data(word_counts)
    elif question.question_type in (Question.TYPE_MULTIPLE_CHOICE, Question.TYPE_KEYPAD, Question.TYPE_MENU):
        category_counts = pollrun.get_answer_category_counts(question, regions)
        chart_type = 'pie'
        chart_data = pie_chart_data(category_counts)
    elif question.question_type == Question.TYPE_NUMERIC:
        range_counts = pollrun.get_answer_auto_range_counts(question, regions)
        chart_type = 'column'
        chart_data = column_chart_data(range_counts)
    else:
        chart_type = None
        chart_data = []

    return chart_type, render_data(chart_data)


def multiple_pollruns(pollruns, question, regions):
    if question.question_type == Question.TYPE_NUMERIC:
        return multiple_pollruns_numeric(pollruns, question, regions)
    if question.question_type == Question.TYPE_OPEN:
        return multiple_pollruns_open(pollruns, question, regions)
    if question.question_type == Question.TYPE_MULTIPLE_CHOICE:
        return multiple_pollruns_multiple_choice(pollruns, question, regions)
    return None, None


def multiple_pollruns_open(pollruns, question, regions):
    """Chart data for multiple pollruns of a poll."""
    pollrun_dict = OrderedDict()
    overall_counts = defaultdict(int)
    for pollrun in pollruns:
        word_counts = pollrun.get_answer_word_counts(question, regions)
        for word, count in word_counts:
            overall_counts[word] += count
    sorted_counts = sorted(overall_counts.items(), key=itemgetter(1), reverse=True)
    pollrun_dict = word_cloud_data(sorted_counts[:50])
    return 'open-ended', render_data({
        'words': pollrun_dict,
    })


def multiple_pollruns_multiple_choice(pollruns, question, regions):
    pollrun_dict = OrderedDict()
    answers = Answer.objects.filter(response__pollrun=pollruns, response__is_active=True)
    answers = answers.exclude(response__status=Response.STATUS_EMPTY)
    if regions:
        answers = answers.filter(response__contact__region__in=regions)
    categories = answers.distinct('category')
    categories = categories.order_by('category').values_list('category', flat=True)

    for category in categories:
        answers_category = answers.filter(category=category)
        answers_category_list = []
        for pollrun in pollruns.order_by('conducted_on'):
            answers_category_count = answers_category.filter(response__pollrun=pollrun).count()
            answers_category_list.append(answers_category_count)
        pollrun_dict[category] = answers_category_list
    date_list = [pollrun.conducted.strftime('%Y-%m-%d')
                 for pollrun in pollruns.order_by('conducted_on')]

    return 'multiple-choice', render_data({
        'categories': [d.strftime('%Y-%m-%d') for d in date_list],
        'series': pollrun_dict,
    })


def response_rate_calculation(responses, pollrun_list):
    """Return a list of response rates for the pollruns."""
    # A response is complete if its status attribute equals STATUS_COMPLETE.
    # This uses an internal, _combine, because F expressions have not
    # exposed the SQL '=' operator.
    is_complete = F('status')._combine(Response.STATUS_COMPLETE, '=', False)
    responses = responses.annotate(is_complete=is_complete)

    # Count responses by completion status per pollrun.
    # When an annotation is applied to a values() result, the annotation
    # results are grouped by the unique combinations of the fields specified
    # in the values() clause. Result looks like:
    #   [
    #       {'pollrun': 123, 'is_complete': True, 'count': 5},
    #       {'pollrun': 123, 'is_complete': False, 'count': 10},
    #       {'pollrun': 456, 'is_complete': True, 'count': 7},
    #       {'pollrun': 456, 'is_complete': False, 'count': 12},
    #       ...
    #   ]
    responses = responses.order_by('pollrun')
    responses = responses.values('pollrun', 'is_complete')
    responses = responses.annotate(count=Count('pk'))

    # pollrun id -> response data
    data_by_pollrun = groupby(responses, itemgetter('pollrun'))
    data_by_pollrun = dict((k, list(v)) for k, v in data_by_pollrun)

    response_rates = []
    for pollrun in pollrun_list:
        response_data = data_by_pollrun.get(pollrun)
        if response_data:
            # completion status (True/False) -> count of responses
            count_by_status = dict((c['is_complete'], c['count']) for c in response_data)

            complete_responses = count_by_status.get(True, 0)
            total_responses = sum(count_by_status.values())
            response_rates.append(round(100.0 * complete_responses / total_responses, 2))
        else:
            response_rates.append(0)
    return response_rates


def multiple_pollruns_numeric(pollruns, question, regions):
    """Chart data for multiple pollruns of a poll."""
    responses = Response.objects.filter(pollrun__in=pollruns)
    responses = responses.filter(is_active=True)

    if regions:
        responses = responses.filter(contact__region__in=regions)

    answers = Answer.objects.filter(response__in=responses, question=question)
    answers = answers.select_related('response')
    answers = answers.order_by('response__created_on')

    # Calculate/retrieve the list of sums, list of averages,
    # list of pollrun dates, and list of pollrun id's
    # per pollrun date
    (answer_sum_list, answer_average_list,
        date_list, pollrun_list) = answers.numeric_group_by_date()

    # Calculate the response rate per day
    response_rate_list = list(response_rate_calculation(responses, pollrun_list))

    # Create dict lists for the three datasets for data point/url
    answer_sum_dict_list = []
    answer_average_dict_list = []
    response_rate_dict_list = []
    for z in zip(answer_sum_list, answer_average_list, response_rate_list, pollrun_list):
        pollrun_link_read = reverse('polls.pollrun_read', args=[str(z[3])])
        pollrun_link_participation = reverse('polls.pollrun_participation', args=[str(z[3])])
        answer_sum_dict_list.append(
            {str('y'): z[0], str('url'): pollrun_link_read})
        answer_average_dict_list.append(
            {str('y'): z[1], str('url'): pollrun_link_read})
        response_rate_dict_list.append(
            {str('y'): z[2], str('url'): pollrun_link_participation})

    question.answer_mean = round(numpy.mean(answer_average_list), 2)
    question.answer_stdev = round(numpy.std(answer_average_list), 2)
    question.response_rate_average = round(numpy.mean(response_rate_list), 2)
    return 'numeric', render_data({
        'categories': [d.strftime('%Y-%m-%d') for d in date_list],
        'sum': answer_sum_dict_list,
        'average': answer_average_dict_list,
        'response-rate': response_rate_dict_list,
    })


def word_cloud_data(word_counts):
    return [{'text': word, 'weight': count} for word, count in word_counts]


def pie_chart_data(category_counts):
    return [[cgi.escape(category), count] for category, count in category_counts]


def column_chart_data(range_counts):
    # highcharts needs the category labels and values separate for column charts
    if range_counts:
        labels, counts = zip(*range_counts)
        return [cgi.escape(l) for l in labels], counts
    else:
        return []


def render_data(chart_data):
    return mark_safe(json.dumps(chart_data, cls=ChartJsonEncoder))
