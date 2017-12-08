from __future__ import unicode_literals

from decimal import InvalidOperation
import re

import numpy
import pycountry
import stop_words


def extract_words(text, language):
    """
    Extracts significant words from the given text (i.e. words we want to
    include in a word cloud)
    """
    ignore_words = []
    if language:
        code = pycountry.languages.get(bibliographic=language).alpha2
        try:
            ignore_words = stop_words.get_stop_words(code)
        except stop_words.StopWordError:
            pass

    words = re.split(r"[^\w'-]", text.lower(), flags=re.UNICODE)
    ignore_words = ignore_words
    return [w for w in words if w not in ignore_words and len(w) > 1]


def _convert(text):
    """If text is numeric, convert to an integer. Otherwise, force lowercase."""
    return int(text) if text.isdigit() else text.lower()


def natural_sort_key(text):
    """Key to sort text in a humanized way, e.g., 11 should come before 100."""
    text = text or ""  # can't split None
    alphanumeric_parts = re.split("([0-9]+)", text)  # ab12cd34 -> ["ab", "12", "cd", "34", ""]
    return [_convert(t) for t in alphanumeric_parts if t]


def get_numeric_values(values):
    """Return all values that can be parsed as a float."""
    numeric = []
    for val in values:
        try:
            numeric.append(float(val))
        except (TypeError, ValueError, InvalidOperation):
            pass
    return numeric


def summarize_by_pollrun(answers, responses):
    answer_values = answers.group_values('response__pollrun_id')
    response_counts = responses.group_counts('pollrun')

    answer_sums = {}
    answer_avgs = {}
    answer_stdevs = {}
    response_rates = {}

    # Note: Each pollrun has response(s), even if it has no answer(s) -
    # so iterating over the response pollruns will cover all pollruns.
    for pollrun_id, response_count in response_counts.items():
        values = answer_values.get(pollrun_id, [])
        (answer_sums[pollrun_id],
         answer_avgs[pollrun_id],
         answer_stdevs[pollrun_id],
         response_rates[pollrun_id]) = _summarize(values, response_count)

    return answer_sums, answer_avgs, answer_stdevs, response_rates


def summarize_by_region_and_pollrun(answers, responses):
    answer_values = answers.group_values(
        'response__contact__region_id', 'response__pollrun_id')
    response_counts = responses.group_counts(
        'contact__region', 'pollrun')

    data = {}
    for (region_id, pollrun_id), response_count in response_counts.items():
        data.setdefault(region_id, ({}, {}, {}, {}))
        values = answer_values.get((region_id, pollrun_id), [])
        (data[region_id][0][pollrun_id],
         data[region_id][1][pollrun_id],
         data[region_id][2][pollrun_id],
         data[region_id][3][pollrun_id]) = _summarize(values, response_count)
    return data


def _summarize(values, response_count):
    numeric_values = get_numeric_values(values)

    answer_sum = round(numpy.sum(numeric_values), 1)
    answer_avg = round(numpy.mean(numeric_values) if numeric_values else 0, 1)
    answer_stdev = round(numpy.std(numeric_values) if numeric_values else 0, 1)
    response_rate = round(100.0 * len(values) / response_count, 1)

    return answer_sum, answer_avg, answer_stdev, response_rate


def overall_mean(pollruns, data, default=0, round_to=1):
    """Return the mean of data values for each pollrun."""
    padded_data = [data.get(pollrun.pk, default) for pollrun in pollruns]
    return round(numpy.mean(padded_data), round_to)


def overall_stdev(pollruns, data, default=0, round_to=1):
    """Return the standard deviation of data values for each pollrun."""
    padded_data = [data.get(pollrun.pk, default) for pollrun in pollruns]
    return round(numpy.std(padded_data), round_to)
