from __future__ import absolute_import, unicode_literals

from tracpro.charts.formatters import format_series, format_x_axis

from .models import Answer, Question
from .utils import summarize, overall_mean, overall_stdev


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

            _, answer_avgs, answer_stdevs, response_rates = summarize(answers, responses)
            summary_table = [
                ('Mean', answer_avgs.get(pollrun.pk, 0)),
                ('Standard deviation', answer_stdevs.get(pollrun.pk, 0)),
                ('Response rate average', response_rates.get(pollrun.pk, 0)),
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
            (answer_sums,
             answer_avgs,
             answer_stdevs,
             response_rates) = summarize(answers, responses)

            chart_type = 'numeric'
            chart_data = multiple_pollruns_numeric(
                pollruns, answer_sums, answer_avgs, response_rates)
            summary_table = [
                ('Mean', overall_mean(pollruns, answer_avgs)),
                ('Standard deviation', overall_stdev(pollruns, answer_avgs)),
                ('Response rate average', overall_mean(pollruns, response_rates)),
            ]

        elif question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            chart_data = word_cloud_data(answers)

        elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
            (answer_sums,
             answer_avgs,
             answer_stdevs,
             response_rates) = summarize(answers, responses)

            chart_type = 'multiple-choice'
            chart_data = multiple_pollruns_multiple_choice(pollruns, answers)
            summary_table = [
                ('Mean', overall_mean(pollruns, answer_avgs)),
                ('Standard deviation', overall_stdev(pollruns, answer_avgs)),
                ('Response rate average', overall_mean(pollruns, response_rates)),
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


def multiple_pollruns_numeric(pollruns, answer_sums, answer_avgs, response_rates):
    """Chart data for multiple pollruns of a poll."""
    return {
        'dates': format_x_axis(pollruns),
        'sum': format_series(pollruns, answer_sums,
                             url='id@polls.pollrun_read'),
        'average': format_series(pollruns, answer_avgs,
                                 url='id@polls.pollrun_read'),
        'response-rate': format_series(pollruns, response_rates,
                                       url='id@polls.pollrun_participation'),
    }
