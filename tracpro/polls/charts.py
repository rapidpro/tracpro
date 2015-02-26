from __future__ import absolute_import, unicode_literals

import cgi
import datetime
import json
import operator

from collections import defaultdict, OrderedDict
from dash.utils import datetime_to_ms
from django.utils.safestring import mark_safe
from .models import QUESTION_TYPE_OPEN, QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_NUMERIC


class ChartJsonEncoder(json.JSONEncoder):
    """
    JSON Encoder which encodes datetime objects millisecond timestamps. Used for highcharts.js data.
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ms(obj)
        return json.JSONEncoder.default(self, obj)


def single_issue(issue, question, region):
    """
    Chart data for a single issue. Will be a word cloud for open-ended questions, and pie chart of categories for
    everything else.
    """
    aggregates = issue.get_answer_aggregates(question, region)

    if question.type == QUESTION_TYPE_OPEN:
        chart_data = word_cloud_data(aggregates)
    elif question.type == QUESTION_TYPE_MULTIPLE_CHOICE:
        chart_data = pie_chart_data(aggregates)
    elif question.type == QUESTION_TYPE_NUMERIC:
        chart_data = column_chart_data(aggregates)
    else:
        chart_data = []

    return render_data(chart_data)


def multiple_issues(issues, question, region):
    """
    Chart data for multiple issues of a poll.
    """
    if question.type == QUESTION_TYPE_OPEN:
        overall_counts = defaultdict(int)

        for issue in issues:
            aggregates = issue.get_answer_aggregates(question, region)
            for word, count in aggregates:
                overall_counts[word] += count

        sorted_counts = sorted(overall_counts.items(), key=operator.itemgetter(1), reverse=True)
        chart_data = word_cloud_data(sorted_counts[:50])
    else:
        categories = set()
        counts_by_issue = OrderedDict()

        # fetch category counts for all issues, keeping track of all found categories
        for issue in issues:
            aggregates = issue.get_answer_aggregates(question, region)
            as_dict = dict(aggregates)
            counts_by_issue[issue] = as_dict

            for category in as_dict.keys():
                categories.add(category)

        categories = list(categories)
        category_series = defaultdict(list)

        for issue, category_counts in counts_by_issue.iteritems():
            for category in categories:
                count = category_counts.get(category, 0)
                category_series[category].append((issue.conducted_on, count))

        chart_data = [{'name': cgi.escape(category), 'data': data} for category, data in category_series.iteritems()]

    return render_data(chart_data)


def word_cloud_data(aggregates):
    return [{'text': word, 'weight': count} for word, count in aggregates]


def pie_chart_data(aggregates):
    return [[cgi.escape(category), count] for category, count in aggregates]


def column_chart_data(aggregates):
    # highcharts needs the category labels and values separate for column charts
    labels, counts = zip(*aggregates)
    return [cgi.escape(l) for l in labels], counts


def render_data(chart_data):
    return mark_safe(json.dumps(chart_data, cls=ChartJsonEncoder))

