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
    if question.type == Question.TYPE_OPEN:
        word_counts = pollrun.get_answer_word_counts(question, regions)
        chart_type = 'word'
        chart_data = word_cloud_data(word_counts)
    elif question.type in (Question.TYPE_MULTIPLE_CHOICE, Question.TYPE_KEYPAD, Question.TYPE_MENU):
        category_counts = pollrun.get_answer_category_counts(question, regions)
        chart_type = 'pie'
        chart_data = pie_chart_data(category_counts)
    elif question.type == Question.TYPE_NUMERIC:
        range_counts = pollrun.get_answer_auto_range_counts(question, regions)
        chart_type = 'column'
        chart_data = column_chart_data(range_counts)
    else:
        chart_type = None
        chart_data = []

    return chart_type, render_data(chart_data)


def multiple_pollruns_old(pollruns, question, regions):
    """Chart data for multiple pollruns of a poll."""

    if question.type == Question.TYPE_OPEN:
        overall_counts = defaultdict(int)

        for pollrun in pollruns:
            word_counts = pollrun.get_answer_word_counts(question, regions)
            for word, count in word_counts:
                overall_counts[word] += count

        sorted_counts = sorted(
            overall_counts.items(), key=itemgetter(1), reverse=True)
        chart_type = 'word'
        chart_data = word_cloud_data(sorted_counts[:50])
    elif question.type == Question.TYPE_MULTIPLE_CHOICE:
        categories = set()
        counts_by_pollrun = OrderedDict()

        # fetch category counts for all pollruns, keeping track of all found
        # categories
        for pollrun in pollruns:
            category_counts = pollrun.get_answer_category_counts(question, regions)
            as_dict = dict(category_counts)
            counts_by_pollrun[pollrun] = as_dict

            for category in as_dict.keys():
                categories.add(category)

        categories = list(categories)
        category_series = defaultdict(list)

        for pollrun, category_counts in counts_by_pollrun.iteritems():
            for category in categories:
                count = category_counts.get(category, 0)
                category_series[category].append((pollrun.conducted_on, count))

        chart_type = 'time-area'
        chart_data = [{'name': cgi.escape(category), 'data': data}
                      for category, data in category_series.iteritems()]
    elif question.type == Question.TYPE_NUMERIC:
        chart_type = 'time-line'
        chart_data = []
        for pollrun in pollruns:
            average = pollrun.get_answer_numeric_average(question, regions)
            chart_data.append((pollrun.conducted_on, average))
    else:
        chart_type = None
        chart_data = []

    return chart_type, render_data(chart_data)


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


def multiple_pollruns(pollruns, question, regions):
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

    # Calculate the mean, standard deviation and average response rate to display
    answer_mean = round(numpy.mean(answer_average_list), 2)
    answer_stdev = round(numpy.std(answer_average_list), 2)
    response_rate_average = round(numpy.mean(response_rate_list), 2)

    return (answer_sum_list, answer_average_list, response_rate_list, date_list,
            answer_mean, answer_stdev, response_rate_average)


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
