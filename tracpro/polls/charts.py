from __future__ import absolute_import, unicode_literals

import cgi
import datetime
from decimal import Decimal
from itertools import groupby
import json
import numpy
from operator import itemgetter

from dash.utils import datetime_to_ms

from django.db.models import Count, F
from django.core.urlresolvers import reverse

from .models import Answer, Question, Response, PollRun


class ChartJsonEncoder(json.JSONEncoder):
    """Encode millisecond timestamps & Decimal objects as floats."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ms(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def single_pollrun(pollrun, question, answer_filters):
    """Chart data for a single pollrun.

    Will be a word cloud for open-ended questions, and pie chart of categories
    for everything else.
    """
    chart_type = None
    chart_data = []

    pollruns = PollRun.objects.filter(pk=pollrun.pk)
    answers = get_answers(pollruns, question, answer_filters)
    chart_data_exists = False
    if question.question_type == Question.TYPE_OPEN:
        chart_type = 'open-ended'
        chart_data = multiple_pollruns_open(answers, pollruns, question)
        if chart_data:
            chart_data_exists = True
    else:
        chart_type = 'bar'
        chart_data = single_pollrun_multiple_choice(answers, pollrun)
        if chart_data['data']:
            chart_data_exists = True

    return chart_type, render_data(chart_data), chart_data_exists


def single_pollrun_multiple_choice(answers, pollrun):
    data = []
    categories = []
    for category, pollrun_counts in answers.category_counts_by_pollrun():
        categories.append(category)
        count = pollrun_counts.get(pollrun.pk, 0)
        data.append(count)

    return {
        'categories': categories,
        'data': data,
    }


def multiple_pollruns(pollruns, question, answer_filters):
    chart_type = None
    data = None

    pollruns = pollruns.order_by('conducted_on')
    answers = get_answers(pollruns, question, answer_filters)
    if answers:
        if question.question_type == Question.TYPE_NUMERIC:
            chart_type = 'numeric'
            data = multiple_pollruns_numeric(answers, pollruns, question)

        elif question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            data = multiple_pollruns_open(answers, pollruns, question)

        elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
            chart_type = 'multiple-choice'
            data = multiple_pollruns_multiple_choice(answers, pollruns, question)

    return chart_type, render_data(data) if data else None


def get_answers(pollruns, question, filters):
    """Return all Answers to the question within the pollruns.

    If regions are specified, answers are limited to contacts within those
    regions.
    """
    return Answer.objects.filter(
        filters,
        response__pollrun__in=pollruns,
        question=question)


def multiple_pollruns_open(answers, pollruns, question):
    """Chart data for multiple pollruns of a poll."""
    return word_cloud_data(answers.word_counts())


def multiple_pollruns_multiple_choice(answers, pollruns, question):
    series = []
    for category, pollrun_counts in answers.category_counts_by_pollrun():
        data = []
        for pollrun in pollruns:
            count = pollrun_counts.get(pollrun.pk, 0)
            url = reverse('polls.pollrun_read', args=[pollrun.pk])
            data.append({'y': count, 'url': url})
        series.append({
            'name': category,
            'data': data,
        })

    dates = [pollrun.conducted_on.strftime('%Y-%m-%d') for pollrun in pollruns]

    return {
        'dates': dates,
        'series': series,
    }


def response_rate_calculation(responses):
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

    response_rates = {}
    for pollrun_id, data in groupby(responses, itemgetter('pollrun')):
        # completion status (True/False) -> response count
        completion = {d['is_complete']: d['count'] for d in data}
        complete = completion.get(True, 0)
        incomplete = completion.get(False, 0)
        response_rates[pollrun_id] = round(100.0 * complete / (complete + incomplete), 2)
    return response_rates


def multiple_pollruns_numeric(answers, pollruns, question):
    """Chart data for multiple pollruns of a poll."""
    answers = answers.select_related('response')

    # Calculate/retrieve the list of sums, list of averages,
    # list of pollrun dates, and list of pollrun id's
    # per pollrun date
    summaries = answers.get_answer_summaries()

    # Calculate the response rate on each day
    responses = Response.objects.filter(answers=answers).distinct()
    response_rate_data = response_rate_calculation(responses)

    answer_sums = []
    answer_avgs = []
    response_rates = []
    for pollrun in pollruns:
        answer_sum, answer_avg = summaries.get(pollrun.pk, (0, 0))
        response_rate = response_rate_data.get(pollrun.pk, 0)
        pollrun_detail = reverse('polls.pollrun_read', args=[pollrun.pk])
        pollrun_participation = reverse('polls.pollrun_participation', args=[pollrun.pk])
        answer_sums.append({'y': answer_sum, 'url': pollrun_detail})
        answer_avgs.append({'y': answer_avg, 'url': pollrun_detail})
        response_rates.append({'y': response_rate, 'url': pollrun_participation})

    question.answer_mean = round(numpy.mean([a['y'] for a in answer_avgs]), 2)
    question.answer_stdev = round(numpy.std([a['y'] for a in answer_avgs]), 2)
    question.response_rate_average = round(numpy.mean([a['y'] for a in response_rates]), 2)

    return {
        'dates': [pollrun.conducted_on.strftime('%Y-%m-%d') for pollrun in pollruns],
        'sum': answer_sums,
        'average': answer_avgs,
        'response-rate': response_rates,
    }


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
    return json.dumps(chart_data, cls=ChartJsonEncoder)
