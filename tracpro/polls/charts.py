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
        chart_type = 'numeric'
        data = multiple_pollruns_numeric(pollruns, question, regions)

    elif question.question_type == Question.TYPE_OPEN:
        chart_type = 'open-ended'
        data = multiple_pollruns_open(pollruns, question, regions)

    elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
        chart_type = 'multiple-choice'
        data = multiple_pollruns_multiple_choice(pollruns, question, regions)

    else:
        chart_type = None
        data = None

    return chart_type, render_data(data) if data else None


def get_answers(pollruns, question, regions):
    """Return all Answers to the question within the pollruns.

    If regions are specified, answers are limited to contacts within those
    regions.
    """
    answers = Answer.objects.filter(
        response__pollrun__in=pollruns,
        response__is_active=True,
        question=question)
    if regions:
        answers = answers.filter(response__contact__region__in=regions)
    return answers


def multiple_pollruns_open(pollruns, question, regions):
    """Chart data for multiple pollruns of a poll."""
    answers = get_answers(pollruns, question, regions)
    return word_cloud_data(answers.word_counts()) if answers else None


def multiple_pollruns_multiple_choice(pollruns, question, regions):
    answers = get_answers(pollruns, question, regions)
    pollruns = pollruns.order_by('conducted_on')

    if answers:
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
    return None


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


def multiple_pollruns_numeric(pollruns, question, regions):
    """Chart data for multiple pollruns of a poll."""
    answers = get_answers(pollruns, question, regions)
    answers = answers.select_related('response')
    answers = answers.order_by('response__created_on')

    if answers:
        # Calculate/retrieve the list of sums, list of averages,
        # list of pollrun dates, and list of pollrun id's
        # per pollrun date
        (answer_sum_list, answer_average_list,
            date_list, pollrun_list) = answers.numeric_group_by_date()

        # Calculate the response rate on each day
        responses = Response.objects.filter(answers=answers).distinct()
        response_rates = response_rate_calculation(responses)
        response_rate_list = [response_rates.get(pollrun.pk, 0) for pollrun in pollruns]

        # Create dict lists for the three datasets for data point/url
        answer_sum_dict_list = []
        answer_average_dict_list = []
        response_rate_dict_list = []
        for z in zip(answer_sum_list, answer_average_list, response_rate_list, pollrun_list):
            answer_sum, answer_average, response_rate, pollrun_id = z
            pollrun_detail = reverse('polls.pollrun_read', args=[pollrun_id])
            pollrun_participation = reverse('polls.pollrun_participation', args=[pollrun_id])
            answer_sum_dict_list.append(
                {'y': answer_sum, 'url': pollrun_detail})
            answer_average_dict_list.append(
                {'y': answer_average, 'url': pollrun_detail})
            response_rate_dict_list.append(
                {'y': response_rate, 'url': pollrun_participation})

        question.answer_mean = round(numpy.mean(answer_average_list), 2)
        question.answer_stdev = round(numpy.std(answer_average_list), 2)
        question.response_rate_average = round(numpy.mean(response_rate_list), 2)
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in date_list],
            'sum': answer_sum_dict_list,
            'average': answer_average_dict_list,
            'response-rate': response_rate_dict_list,
        }
    return None


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
