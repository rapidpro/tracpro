from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta

import numpy

from tracpro.charts.formatters import format_series, format_x_axis
from tracpro.polls.utils import (
    get_numeric_values, summarize_by_pollrun, overall_mean, overall_stdev)


def chart_baseline(baseline_term, filter_form, region, include_subregions):
    start_date = filter_form.cleaned_data['start_date']
    end_date = filter_form.cleaned_data['end_date']

    # NOTE: region and include_subregions act on the PollRun region, and
    # should come from the request. The filter form may do additional
    # filtering by contact region.
    kwargs = {
        'start_date': start_date,
        'end_date': end_date,
        'region': region,  # pollrun region
        'include_subregions': include_subregions,
        'contacts': filter_form.filter_contacts(),
    }

    (follow_up_pollruns,
     follow_up_series,
     follow_up_mean,
     follow_up_stdev,
     follow_up_response_rate) = get_follow_up_data(baseline_term, **kwargs)

    if not follow_up_pollruns:
        # No data to display.
        return None, None

    goal = filter_form.cleaned_data.get('goal')
    if goal is not None:
        # Use the user-specified goal as the baseline.
        baseline = goal
        baseline_response_rate = None  # not applicable
    else:
        baseline, baseline_response_rate = get_baseline_data(baseline_term, **kwargs)

    # Create a series using the baseline value to match the length of the
    # follow up series.
    baseline_series = {
        'name': "Baseline",
        'data': [baseline] * len(follow_up_pollruns),
    }

    chart_data = {
        'series': [baseline_series, follow_up_series],
        'categories': format_x_axis(follow_up_pollruns),
    }

    summary_table = [
        ("Dates", "{} - {}".format(
            start_date.strftime("%B %d, %Y"),
            (end_date - relativedelta(days=1)).strftime("%B %d, %Y"),
        )),
        ("Baseline question", "{}: {}".format(
            baseline_term.baseline_poll.name,
            baseline_term.baseline_question.name,
        )),
        ("Baseline value ({})".format(baseline_term.y_axis_title), baseline),
        ("Baseline response rate (%)", baseline_response_rate),
        ("Follow up question", "{}: {}".format(
            baseline_term.follow_up_poll.name,
            baseline_term.follow_up_question.name,
        )),
        ("Follow up mean ({})".format(baseline_term.y_axis_title), follow_up_mean),
        ("Follow up standard deviation", follow_up_stdev),
        ("Follow up response rate (%)", follow_up_response_rate),
    ]
    return chart_data, summary_table


def get_baseline_data(baseline_term, **kwargs):
    """Return the baseline value and response rate."""
    pollruns, responses, answers = baseline_term.get_baseline_data(**kwargs)

    # The sum of the first answer from each contact.
    answers = answers.order_by('response__contact', 'submitted_on')
    answers = answers.distinct('response__contact')
    numeric_values = get_numeric_values(answers.values_list('value', flat=True))

    baseline = numpy.sum(numeric_values)

    responses = responses.distinct('contact')
    response_rate = round(100.0 * len(answers) / len(responses), 1) if responses else 0.0

    return baseline, response_rate


def get_follow_up_data(baseline_term, **kwargs):
    """Return the follow up pollruns, data series, and summary data."""
    pollruns, responses, answers = baseline_term.get_follow_up_data(**kwargs)
    (answer_sums,
     answer_avgs,
     answer_stdevs,
     response_rates) = summarize_by_pollrun(answers, responses)

    series = format_series(pollruns, answer_sums, name="Follow up")
    mean = overall_mean(pollruns, answer_sums)
    stdev = overall_stdev(pollruns, answer_sums)
    response_rate = overall_mean(pollruns, response_rates)

    return pollruns, series, mean, stdev, response_rate
