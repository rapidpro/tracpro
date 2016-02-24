from __future__ import absolute_import, unicode_literals

import datetime
import json

from decimal import Decimal

from dash.utils import datetime_to_ms


class ChartsJSONEncoder(json.JSONEncoder):
    """Encode millisecond timestamps & Decimal objects as floats."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ms(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def render_data(chart_data):
    return json.dumps(chart_data, cls=ChartsJSONEncoder)


def midnight(d):
    return datetime.datetime(d.year, d.month, d.day, tzinfo=d.tzinfo)
