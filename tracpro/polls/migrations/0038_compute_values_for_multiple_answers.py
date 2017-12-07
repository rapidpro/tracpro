# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from tracpro.polls.utils import get_numeric_values


"""
WARNING: THIS MIGRATION WILL TAKE A LONG TIME FOR REAL DATA.

(As of early December 2017, there are nearly a
million Answers in the database.)

Suggestions to speed it up any more would be welcome.
Maybe some SQL ninja can come up with a SQL statement
to do it all on the server side instead of having to
iterate over all the answers and query almost every
answer individually.
"""

from django.db import migrations
from django.db.models import F

from tracpro.charts.utils import midnight, end_of_day


def compute_values_0038(apps, schema):
    Answer = apps.get_model('polls.Answer')

    # Initialize the new fields to each record's 'value'.
    # We get back the number of updated records for free, so
    # display it to give some clue about how big the rest of the
    # migration is.
    count = Answer.objects.update(last_value=F('value'), sum_value=F('value'))
    print("There are %d answers to look at." % count)

    # Some need to be updated.
    # For each active numeric answer, if there were other answers to the same question on
    # the same day by the same contact, then update all of them.
    # Try it for non-numeric questions too - someday they could change to numeric and
    # otherwise we would not have values to use for them.
    for answer in Answer.objects.filter(response__is_active=True).select_related('response'):
        # All answers by same contact for same question on same day
        answers = Answer.objects.filter(
            question_id=answer.question_id,
            response__contact_id=answer.response.contact_id,
            submitted_on__gte=midnight(answer.submitted_on),
            submitted_on__lte=end_of_day(answer.submitted_on),
        ).order_by('-submitted_on')
        if len(answers) > 1:
            # There was more than one answer by same contact/day/question.
            # Compute last and sum.
            as_floats = get_numeric_values([a.value for a in answers])
            if len(as_floats) > 0:
                sum_value = str(sum(as_floats))
            else:
                sum_value = F('value')  # No valid floats, just use value as-is
            last_value = answers[0].value
            answers.update(last_value=last_value, sum_value=sum_value)


def undo_values_0038(apps, schema):
    Answer = apps.get_model('polls.Answer')
    Answer.objects.update(last_value=None, sum_value=None)


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0037_auto_20171205_1323'),
    ]

    operations = [
        migrations.RunPython(
            compute_values_0038,
            undo_values_0038
        )
    ]
