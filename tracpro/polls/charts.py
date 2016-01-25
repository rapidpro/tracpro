from __future__ import absolute_import, unicode_literals

import numpy

from tracpro.charts.formatters import format_series, format_x_axis
from tracpro.charts.utils import render_data

from .models import Answer, PollRun, Question, Response
from .utils import get_numeric_values


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
        responses = Response.objects.filter(answers=answers).distinct()
        response_rates = responses.get_response_rates()

        answer_avg = answer_avgs.get(pollrun.pk, 0)
        response_rate = response_rates.get(pollrun.pk, 0)
        numeric_values = get_numeric_values(answers.values_list('value', flat=True))
        stdev = round(numpy.std(numeric_values), 2)

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


def multiple_pollruns_numeric(answers, pollruns, question):
    """Chart data for multiple pollruns of a poll."""
    answer_sums, answer_avgs = answers.get_answer_summaries()

    responses = Response.objects.filter(answers=answers).distinct()
    response_rates = responses.get_response_rates()

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
