from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.db.models.functions import Lower
from django.utils.http import urlencode

from tracpro.charts.formatters import format_series, format_x_axis
from tracpro.groups.models import Region

from .models import Answer, Question, SAMEDAY_SUM
from . import utils


def _url(name, args=None, kwargs=None, params=None):
    url = reverse(name, args=args, kwargs=kwargs)
    if params:
        url = '{}?{}'.format(url, urlencode(params))
    return url


def single_pollrun(pollrun, responses, question):
    """Chart the data for one question from a single pollrun.

    Assumes responses are already filtered for the desired pollrun/date,
    and includes all valid answers for the given question and responses.

    Will be a word cloud for open-ended questions, a bar chart with autocreated
    categories for numeric questions, and a bar chart of categories for everything else.

    Returns a tuple (chart_type, chart_data, summary_table), where:

    chart_type = None|'open-ended'|'bar'
    chart_data = {'categories': list of category names, 'data': list of counts} for all but open-ended,
       or list of {'text': 'xxx', 'weight': NNN} dictionaries for open-ended}
       or empty list if there were no answers.
    summary_table = if numeric:
        [('Mean', value), ('Standard deviation', value), ('Response rate average (%)', value)]
        else (no answers or non-numeric) None.
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
            if question.question_type == Question.TYPE_NUMERIC:
                chart_data = single_pollrun_auto_categorize(answers)
            else:
                chart_data = single_pollrun_multiple_choice(answers, pollrun)

            _, answer_avgs, answer_stdevs, response_rates = utils.summarize_by_pollrun(
                answers, responses)
            summary_table = [
                ('Mean', answer_avgs.get(pollrun.pk, 0)),
                ('Standard deviation', answer_stdevs.get(pollrun.pk, 0)),
                ('Response rate average (%)', response_rates.get(pollrun.pk, 0)),
            ]

    return chart_type, chart_data, summary_table


def single_pollrun_auto_categorize(answers):
    return answers.autocategorize()


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


def multiple_pollruns(pollruns, responses, question, split_regions, contact_filters):
    chart_type = None
    chart_data = None
    summary_table = None

    pollruns = pollruns.order_by('conducted_on')
    answers = Answer.objects.filter(response__in=responses, question=question)

    # Save a bit of time with .exists();
    # queryset is re-evaluated later as a values set.
    if answers.exists():
        if question.question_type == Question.TYPE_NUMERIC:
            chart_type = 'numeric'
            if split_regions:
                chart_data, summary_table = multiple_pollruns_numeric_split(
                    pollruns, answers, responses, question, contact_filters)
            else:
                chart_data, summary_table = multiple_pollruns_numeric(
                    pollruns, answers, responses, question, contact_filters)

        elif question.question_type == Question.TYPE_OPEN:
            chart_type = 'open-ended'
            chart_data = word_cloud_data(answers)

        elif question.question_type == Question.TYPE_MULTIPLE_CHOICE:
            chart_type = 'multiple-choice'
            chart_data, summary_table = multiple_pollruns_multiple_choice(
                pollruns, answers, responses, contact_filters)

    return chart_type, chart_data, summary_table


def word_cloud_data(answers):
    """Chart data for multiple pollruns of a poll."""
    return [{'text': word, 'weight': count} for word, count in answers.word_counts()]


def multiple_pollruns_multiple_choice(pollruns, answers, responses, contact_filters):
    series = []
    for category, pollrun_counts in answers.category_counts_by_pollrun():
        series.append(format_series(
            pollruns, pollrun_counts, 'id@polls.pollrun_read', params=contact_filters,
            name=category))

    chart_data = {
        'dates': format_x_axis(pollruns),
        'series': series,
    }

    (answer_sums,
     answer_avgs,
     answer_stdevs,
     response_rates) = utils.summarize_by_pollrun(answers, responses)

    summary_table = [
        ('Mean', utils.overall_mean(pollruns, answer_avgs)),
        ('Standard deviation', utils.overall_stdev(pollruns, answer_avgs)),
        ('Response rate average (%)', utils.overall_mean(pollruns, response_rates)),
    ]

    return chart_data, summary_table


def multiple_pollruns_numeric(pollruns, answers, responses, question, contact_filters):
    (answer_sums,
     answer_avgs,
     answer_stdevs,
     response_rates) = utils.summarize_by_pollrun(answers, responses)

    sum_data = []
    avg_data = []
    rate_data = []
    pollrun_urls = []
    participation_urls = []
    for pollrun in pollruns:
        sum_data.append(answer_sums.get(pollrun.pk, 0))
        avg_data.append(answer_avgs.get(pollrun.pk, 0))
        rate_data.append(response_rates.get(pollrun.pk, 0))
        pollrun_urls.append(
            _url('polls.pollrun_read', [pollrun.pk], params=contact_filters))
        participation_urls.append(
            _url('polls.pollrun_participation', [pollrun.pk], params=contact_filters))

    chart_data = {
        'dates': format_x_axis(pollruns),
        SAMEDAY_SUM: [{'name': question.name, 'data': sum_data}],
        'average': [{'name': question.name, 'data': avg_data}],
        'response-rate': [{'name': question.name, 'data': rate_data}],
        'pollrun-urls': pollrun_urls,
        'participation-urls': participation_urls,
    }

    summary_table = [
        ('Mean', utils.overall_mean(pollruns, answer_avgs)),
        ('Standard deviation', utils.overall_stdev(pollruns, answer_avgs)),
        ('Response rate average (%)', utils.overall_mean(pollruns, response_rates)),
    ]

    return chart_data, summary_table


def multiple_pollruns_numeric_split(pollruns, answers, responses, question, contact_filters):
    """Return separate series for each contact region."""
    data = utils.summarize_by_region_and_pollrun(answers, responses)

    sum_data = []
    avg_data = []
    rate_data = []
    regions = (Region.objects.filter(pk__in=data.keys()).order_by(Lower('name')))
    for region in regions:
        answer_sums, answer_avgs, answer_stdevs, response_rates = data.get(region.pk)
        region_answer_sums = []
        region_answer_avgs = []
        region_response_rates = []
        for pollrun in pollruns:
            region_answer_sums.append(answer_sums.get(pollrun.pk, 0))
            region_answer_avgs.append(answer_avgs.get(pollrun.pk, 0))
            region_response_rates.append(response_rates.get(pollrun.pk, 0))

        sum_data.append({'name': region.name, 'data': region_answer_sums})
        avg_data.append({'name': region.name, 'data': region_answer_avgs})
        rate_data.append({'name': region.name, 'data': region_response_rates})

    pollrun_urls = [
        _url('polls.pollrun_read', [p.pk], params=contact_filters)
        for p in pollruns]
    participation_urls = [
        _url('polls.pollrun_participation', [p.pk], params=contact_filters)
        for p in pollruns]
    chart_data = {
        'dates': format_x_axis(pollruns),
        SAMEDAY_SUM: sum_data,
        'average': avg_data,
        'response-rate': rate_data,
        'pollrun-urls': pollrun_urls,
        'participation-urls': participation_urls,
    }

    (pollrun_answer_sums,
     pollrun_answer_avgs,
     pollrun_answer_stdevs,
     pollrun_response_rates) = utils.summarize_by_pollrun(answers, responses)
    summary_table = [
        ('Mean', utils.overall_mean(pollruns, pollrun_answer_avgs)),
        ('Standard deviation', utils.overall_stdev(pollruns, pollrun_answer_avgs)),
        ('Response rate average (%)', utils.overall_mean(pollruns, pollrun_response_rates)),
    ]

    return chart_data, summary_table
