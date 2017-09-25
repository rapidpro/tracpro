import datetime
from pytz import timezone
from django.test import TestCase
from django.utils.timezone import make_aware

from tracpro.charts.utils import end_of_day, midnight


class EndOfDayTest(TestCase):
    def test_end_of_day_naive(self):
        d = datetime.datetime(1992, 2, 28, 3, 0, 5)
        e = end_of_day(d)
        self.assertEqual('1992-02-28 23:59:59', e.isoformat(' '))

    def test_midnight_naive(self):
        d = datetime.datetime(1992, 2, 28, 3, 0, 5)
        e = midnight(d)
        self.assertEqual('1992-02-28 00:00:00', e.isoformat(' '))

    def test_end_of_day_aware(self):
        d = make_aware(datetime.datetime(1992, 2, 28, 3, 0, 5), timezone('US/Eastern'))
        e = end_of_day(d)
        self.assertEqual('1992-02-28 23:59:59-05:00', e.isoformat(' '))

    def test_midnight_aware(self):
        d = make_aware(datetime.datetime(1992, 2, 28, 3, 0, 5), timezone('US/Eastern'))
        e = midnight(d)
        self.assertEqual('1992-02-28 00:00:00-05:00', e.isoformat(' '))
