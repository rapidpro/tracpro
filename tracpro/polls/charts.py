from __future__ import absolute_import, unicode_literals

import cgi
import datetime
import json
import operator

from collections import defaultdict, OrderedDict
from dash.utils import datetime_to_ms
from django.utils.safestring import mark_safe
from .models import QUESTION_TYPE_OPEN


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
    if question.type == QUESTION_TYPE_OPEN:
        word_counts = issue.get_answer_word_counts(question, region)
        chart_data = word_count_data(word_counts)
    else:
        category_counts = issue.get_answer_category_counts(question, region)
        chart_data = [[cgi.escape(category), count] for category, count in category_counts.iteritems()]

    return render_data(chart_data)


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
        chart_data = word_count_data(sorted_counts[:50])
    else:
        categories = set()
        counts_by_issue = OrderedDict()

        # fetch category counts for all issues, keeping track of all found categories
        for issue in issues:
            category_counts = issue.get_answer_category_counts(question, region)
            counts_by_issue[issue] = category_counts

            for category in category_counts.keys():
                categories.add(category)

        categories = list(categories)
        category_series = defaultdict(list)

        for issue, category_counts in counts_by_issue.iteritems():
            for category in categories:
                count = category_counts.get(category, 0)
                category_series[category].append((issue.conducted_on, count))

        chart_data = [{'name': cgi.escape(category), 'data': data} for category, data in category_series.iteritems()]

    return render_data(chart_data)


def render_data(chart_data):
    return mark_safe(json.dumps(chart_data, cls=ChartJsonEncoder))


def word_count_data(word_counts):
    return [{'text': word, 'weight': count} for word, count in word_counts]

