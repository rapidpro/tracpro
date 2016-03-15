from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.formats import number_format
from django.utils.http import urlencode


def format_number(number, digits):
    return number_format(number, digits, force_grouping=True)


def format_series(pollruns, data, url=None, filters=None, **extra):
    """Format a series of data. A point will be created for each pollrun.

    If a url is provided, each point will be a link.
    """
    def format_point(pollrun):
        point = {'y': data.get(pollrun.pk, 0)}
        if url:
            point['url'] = "{}?{}".format(reverse(url, args=[pollrun.pk]), urlencode(filters))
        return point

    extra['data'] = [format_point(pollrun) for pollrun in pollruns]
    return extra


def format_x_axis(pollruns):
    return [pollrun.conducted_on.strftime('%Y-%m-%d') for pollrun in pollruns]
