from __future__ import absolute_import, unicode_literals

import cgi
import datetime
import json
import operator

from collections import defaultdict, OrderedDict
from dash.utils import datetime_to_ms
from decimal import Decimal
from django.utils.safestring import mark_safe
from .models import QUESTION_TYPE_OPEN, QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_NUMERIC


class ChartJsonEncoder(json.JSONEncoder):
    """
    JSON Encoder which encodes datetime objects millisecond timestamps and Decimal objects as floats
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ms(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def single_issue(issue, question, region):
    """
    Chart data for a single issue. Will be a word cloud for open-ended questions, and pie chart of categories for
    everything else.
    """
    if question.type == QUESTION_TYPE_OPEN:
        word_counts = issue.get_answer_word_counts(question, region)
        chart_type = 'word'
        chart_data = word_cloud_data(word_counts)
    elif question.type == QUESTION_TYPE_MULTIPLE_CHOICE:
        category_counts = issue.get_answer_category_counts(question, region)
        chart_type = 'pie'
        chart_data = pie_chart_data(category_counts)
    elif question.type == QUESTION_TYPE_NUMERIC:
        range_counts = issue.get_answer_range_counts(question, region)
        chart_type = 'column'
        chart_data = column_chart_data(range_counts)
    else:
        chart_type = None
        chart_data = []

    return chart_type, render_data(chart_data)


def multiple_issues(issues, question, region):
    """
    Chart data for multiple issues of a poll.
    """
    if question.type == QUESTION_TYPE_OPEN:
        overall_counts = defaultdict(int)

        for issue in issues:
            word_counts = issue.get_answer_word_counts(question, region)
            for word, count in word_counts:
                overall_counts[word] += count

        sorted_counts = sorted(overall_counts.items(), key=operator.itemgetter(1), reverse=True)
        chart_type = 'word'
        chart_data = word_cloud_data(sorted_counts[:50])
    elif question.type == QUESTION_TYPE_MULTIPLE_CHOICE:
        categories = set()
        counts_by_issue = OrderedDict()

        # fetch category counts for all issues, keeping track of all found categories
        for issue in issues:
            category_counts = issue.get_answer_category_counts(question, region)
            as_dict = dict(category_counts)
            counts_by_issue[issue] = as_dict

            for category in as_dict.keys():
                categories.add(category)

        categories = list(categories)
        category_series = defaultdict(list)

        for issue, category_counts in counts_by_issue.iteritems():
            for category in categories:
                count = category_counts.get(category, 0)
                category_series[category].append((issue.conducted_on, count))

        chart_type = 'time-area'
        chart_data = [{'name': cgi.escape(category), 'data': data} for category, data in category_series.iteritems()]
    elif question.type == QUESTION_TYPE_NUMERIC:
        chart_type = 'time-line'
        chart_data = []
        for issue in issues:
            average = issue.get_answer_numeric_average(question, region)
            chart_data.append((issue.conducted_on, average))
    else:
        chart_type = None
        chart_data = []

    return chart_type, render_data(chart_data)


def word_cloud_data(word_counts):
    return [{'text': word, 'weight': count} for word, count in word_counts]


def pie_chart_data(category_counts):
    return [[cgi.escape(category), count] for category, count in category_counts]


def column_chart_data(range_counts):
    # highcharts needs the category labels and values separate for column charts
    labels, counts = zip(*range_counts)
    return [cgi.escape(l) for l in labels], counts


def render_data(chart_data):
    return mark_safe(json.dumps(chart_data, cls=ChartJsonEncoder))

