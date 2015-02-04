from __future__ import absolute_import, unicode_literals

from django import template

register = template.Library()


@register.filter
def completion_percent(issue, region):
    completion = issue.get_completion(region)
    return int(completion * 100) if completion is not None else 0

@register.filter
def completion_fraction(issue, region):
    complete = issue.get_complete_responses(region).count()
    total = issue.get_responses(region).count()
    return "%d / %d" % (complete, total)
