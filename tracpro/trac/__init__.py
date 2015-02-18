from __future__ import absolute_import, unicode_literals

from django.utils import timezone
from dateutil.relativedelta import relativedelta


def get_month_range(d=None):
    """
    Gets the start (inclusive) and end (exclusive) datetimes of the current month in the same timezone as the given date
    """
    if not d:
        d = timezone.now()

    start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = start + relativedelta(months=1)
    return start, end
