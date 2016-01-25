from __future__ import absolute_import, unicode_literals

from decimal import InvalidOperation
from itertools import groupby
import numpy
from operator import itemgetter

from django.db.models import Count, F

from tracpro.charts.formatters import format_series, format_x_axis
from tracpro.charts.utils import render_data

from .models import Answer, Question, Response, PollRun


def single_pollrun(pollrun, question, answer_filters):
    """Chart data for a single pollrun.

    Will be a word cloud for open-ended questions, and pie chart of categories
    for everything else.
    """
    chart_type = None
    chart_data = []
    answer_avg, response_rate, stdev = [0, 0, 0]

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

    # Calculate the average, standard deviation,
    # and response rate for this pollrun
    if question.question_type != Question.TYPE_OPEN:
        _, answer_avgs = answers.get_answer_summaries()
        answer_avg = answer_avgs.get(pollrun.pk, 0)
        responses = Response.objects.filter(answers=answers).distinct()
        response_rate_data = response_rate_calculation(responses)
        response_rate = response_rate_data.get(pollrun.pk, 0)
        try:
            answer_list = [float(a.value) for a in answers]
            if answer_list:
                stdev = round(numpy.std(answer_list), 2)
            else:
                stdev = 0
        # If any of the values is non-numeric, we cannot calculate the standard deviation
        except (TypeError, ValueError, InvalidOperation):
            stdev = 0

    return chart_type, render_data(chart_data), chart_data_exists, answer_avg, response_rate, stdev


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
            # Call multiple_pollruns_numeric() in order to calculate mean, stdev and resp rate
            multiple_pollruns_numeric(answers, pollruns, question)
            data = multiple_pollruns_multiple_choice(answers, pollruns, question)

    return chart_type, data


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
        series.append({
            'name': category,
            'data': format_series(pollruns, pollrun_counts, url='id@polls.pollrun_read'),
        })

    return {
        'dates': format_x_axis(pollruns),
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
    # Calculate answer sum and answer average per pollrun.
    answers = answers.select_related('response')
    answer_sums, answer_avgs = answers.get_answer_summaries()

    # Calculate response rate per pollrun.
    responses = Response.objects.filter(answers=answers).distinct()
    response_rates = response_rate_calculation(responses)

    sum_data = format_series(pollruns, answer_sums, url='id@polls.pollrun_read')
    avg_data = format_series(pollruns, answer_avgs, url='id@polls.pollrun_read')
    rate_data = format_series(pollruns, response_rates, url='id@polls.pollrun_participation')

    question.answer_mean = round(numpy.mean([a['y'] for a in avg_data]), 2)
    question.answer_stdev = round(numpy.std([a['y'] for a in avg_data]), 2)
    question.response_rate_average = round(numpy.mean([a['y'] for a in rate_data]), 2)

    return {
        'dates': format_x_axis(pollruns),
        'sum': sum_data,
        'average': avg_data,
        'response-rate': rate_data,
    }


def word_cloud_data(word_counts):
    return [{'text': word, 'weight': count} for word, count in word_counts]
