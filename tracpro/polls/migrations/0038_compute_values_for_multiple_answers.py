# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
WARNING: THIS MIGRATION WILL TAKE A LONG TIME FOR REAL DATA.

Suggestions to speed it up any more would be welcome.
Maybe some SQL ninja can come up with a SQL statement
to do it all on the server side instead of having to
iterate over all the answers and query almost every
answer individually.
"""

from django.db import migrations
from django.db.models import F

from tracpro.charts.utils import midnight, end_of_day


TYPE_NUMERIC = 'N'


def compute_values_0038(apps, schema):
    Answer = apps.get_model('polls.Answer')

    # Initialize the new fields to each record's 'value'.
    # We get back the number of updated records for free, so
    # display it to give some clue about how big the rest of the
    # migration is.
    count = Answer.objects.update(last_value=F('value'), sum_value=F('value'))
    print("There are %d answers to look at." % count)

    # Some need to be updated.
    # We ONLY need to update the 'active' ones though - those are the only ones that
    # are actually looked at when we build charts and tables.
    for answer in Answer.objects.filter(question__question_type=TYPE_NUMERIC, response__is_active=True).select_related('response'):
        # All answers by same contact for same question on same day
        answers = Answer.objects.filter(
            question_id=answer.question_id,
            response__contact_id=answer.response.contact_id,
            submitted_on__gte=midnight(answer.submitted_on),
            submitted_on__lte=end_of_day(answer.submitted_on),
        )
        if len(answers) > 1:
            # There was more than one answer by same contact/day/question.
            # Compute last and sum.
            answer.last_value = answers.order_by('-submitted_on')[0].value
            try:
                answer.sum_value = str(sum([float(a.value) for a in answers]))
            except ValueError:
                answer.sum_value = answer.value  # Just use record's value
            answer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0037_auto_20171205_1323'),
    ]

    operations = [
        migrations.RunPython(compute_values_0038, migrations.RunPython.noop),
    ]
