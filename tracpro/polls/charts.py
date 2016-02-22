from __future__ import absolute_import, unicode_literals

import numpy

from tracpro.charts.formatters import format_series, format_x_axis
from tracpro.charts.utils import render_data

from .models import Answer, Question
from .utils import get_numeric_values


def single_pollrun(pollrun, responses, question):
    """Chart data for a single pollrun.

    Will be a word cloud for open-ended questions, and pie chart of categories
    for everything else.
    """
    chart_type = None
    chart_data = []
    summary_table = None

    answers = Answer.objects.filter(response__in=responses, question=question)

    if answers:
        if question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            chart_data = word_cloud_data(answers)
        else:
            chart_type = 'bar'
            chart_data = single_pollrun_multiple_choice(answers, pollrun)

            _, answer_avgs = answers.get_answer_summaries()
            response_rates = responses.get_response_rates()
            answer_avg = answer_avgs.get(pollrun.pk, 0)
            response_rate = response_rates.get(pollrun.pk, 0)
            numeric_values = get_numeric_values(answers.values_list('value', flat=True))
            stdev = round(numpy.std(numeric_values), 2)
            summary_table = [
                ('Mean', answer_avg),
                ('Standard deviation', stdev),
                ('Response rate average', response_rate),
            ]

    return chart_type, chart_data, summary_table


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


def multiple_pollruns(pollruns, responses, question):
    chart_type = None
    chart_data = None
    summary_table = None

    pollruns = pollruns.order_by('conducted_on')
    answers = Answer.objects.filter(response__in=responses, question=question)

    if answers:
        if question.question_type == Question.TYPE_NUMERIC:
            chart_type = 'numeric'
            chart_data = multiple_pollruns_numeric(pollruns, responses, answers, question)
            summary_table = [
                ('Mean', question.answer_mean),
                ('Standard deviation', question.answer_stdev),
                ('Response rate average', question.response_rate_average),
            ]

        elif question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            chart_data = word_cloud_data(answers)

        elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
            chart_type = 'multiple-choice'
            chart_data = multiple_pollruns_multiple_choice(pollruns, answers)

            # Use the side effect of this method to calculate table data.
            # FIXME: This needs to be factored out.
            multiple_pollruns_numeric(pollruns, responses, answers, question)
            summary_table = [
                ('Mean', question.answer_mean),
                ('Standard deviation', question.answer_stdev),
                ('Response rate average', question.response_rate_average),
            ]

    return chart_type, chart_data, summary_table


def word_cloud_data(answers):
    """Chart data for multiple pollruns of a poll."""
    return [{'text': word, 'weight': count} for word, count in answers.word_counts()]


def multiple_pollruns_multiple_choice(pollruns, answers):
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


def multiple_pollruns_numeric(pollruns, responses, answers, question):
    """Chart data for multiple pollruns of a poll."""
    answer_sums, answer_avgs = answers.get_answer_summaries()
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
