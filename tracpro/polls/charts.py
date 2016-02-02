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
    answer_avg, response_rate, stdev = [0, 0, 0]

    answers = Answer.objects.filter(response__in=responses, question=question)
    chart_data_exists = False
    if question.question_type == Question.TYPE_OPEN:
        chart_type = 'open-ended'
        chart_data = word_cloud_data(answers)
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
        response_rates = responses.get_response_rates(split_regions=False)

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


def multiple_pollruns(pollruns, responses, question, split_regions):
    chart_type = None
    data = None

    pollruns = pollruns.order_by('conducted_on')

    answers = Answer.objects.filter(response__in=responses, question=question)

    if answers:
        if question.question_type == Question.TYPE_NUMERIC:
            if split_regions:
                chart_type = 'numeric-split'
            else:
                chart_type = 'numeric'
            data = multiple_pollruns_numeric(pollruns, responses, answers, question, split_regions)

        elif question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            data = word_cloud_data(answers)

        elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
            chart_type = 'multiple-choice'
            # Call multiple_pollruns_numeric() in order to calculate mean, stdev and resp rate
            multiple_pollruns_numeric(pollruns, responses, answers, question, split_regions)
            data = multiple_pollruns_multiple_choice(pollruns, answers)

    return chart_type, data


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


def multiple_pollruns_numeric(pollruns, responses, answers, question, split_regions):
    """Chart data for multiple pollruns of a poll."""
    if split_regions:
        answer_sums_list, answer_avgs_list = answers.get_answer_summaries_regions()
        sum_data_list = []
        avg_data_list = []
        region_list = []
        avgs_list = []
        all_rates_list = []
        for answer_sums, answer_avgs in zip(answer_sums_list, answer_avgs_list):
            sum_data = format_series(pollruns, answer_sums, url='id@polls.pollrun_read')
            avg_data = format_series(pollruns, answer_avgs, url='id@polls.pollrun_read')
            sum_data_list.append(sum_data)
            avg_data_list.append(avg_data)
            region_list.append(answer_sums['region'])
            # Get the averages list for the mean and stdev calculations
            answer_sums.pop('region', 0)  # Pop out the region from the list of averages
            avgs_list = avgs_list + answer_sums.values()
        response_rate_list = responses.get_response_rates(split_regions)
        rate_list = []
        for rates in response_rate_list:
            rate_data = format_series(pollruns, rates, url='id@polls.pollrun_participation')
            rate_list.append(rate_data)
            all_rates_list = all_rates_list + rates.values()
        # Calculate mean, stdev and response rate average
        question.answer_mean = round(numpy.mean(avgs_list), 2)
        question.answer_stdev = round(numpy.std(avgs_list), 2)
        question.response_rate_average = round(numpy.mean(all_rates_list), 2)

    else:
        answer_sums, answer_avgs = answers.get_answer_summaries()

        response_rates = responses.get_response_rates(split_regions)

        sum_data = format_series(pollruns, answer_sums, url='id@polls.pollrun_read')
        avg_data = format_series(pollruns, answer_avgs, url='id@polls.pollrun_read')
        rate_data = format_series(pollruns, response_rates, url='id@polls.pollrun_participation')

        question.answer_mean = round(numpy.mean([a['y'] for a in avg_data]), 2)
        question.answer_stdev = round(numpy.std([a['y'] for a in avg_data]), 2)
        question.response_rate_average = round(numpy.mean([a['y'] for a in rate_data]), 2)

    return {
        'dates': format_x_axis(pollruns),
        'sum': sum_data_list if split_regions else sum_data,
        'average': avg_data_list if split_regions else avg_data,
        'response-rate': rate_list if split_regions else rate_data,
        'region-list': region_list if split_regions else []
    }
