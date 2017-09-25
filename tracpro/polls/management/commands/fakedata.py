#
# Create some fake data to test pollstuff with
# Just for developer use.
#

from random import randint

from dash.orgs.models import Org
from django.core.management.base import LabelCommand
from django.db import transaction
from django.utils.timezone import now

from tracpro.contacts.models import Contact
from tracpro.groups.models import Region, Group
from tracpro.polls.models import Poll, PollRun, Answer, Response, Question


def try_poll(poll):
    try:
        with transaction.atomic():
            region = Region.objects.filter(org=poll.org, is_active=True).first()
            cohort = Group.objects.filter(org=poll.org, is_active=True).first()
            run = PollRun.objects.create(
                pollrun_type=PollRun.TYPE_UNIVERSAL,
                poll=poll,
                region=region,
            )
            if poll.questions.filter(is_active=True).exists() and Contact.objects.filter(org=poll.org).exists():
                question = poll.questions.filter(is_active=True).first()
                question.question_type = Question.TYPE_NUMERIC
                question.save()
                contact = Contact.objects.filter(
                    org=poll.org,
                    is_active=True,
                ).first()
                contact.region = region
                contact.group = cohort
                contact.save()
                contact.groups.add(cohort)
                for i in range(2):
                    response = Response.objects.create(
                        pollrun=run,
                        contact=contact,
                        created_on=now(),
                        updated_on=now(),
                        status=Response.STATUS_COMPLETE,
                        is_active=True if i == 1 else False,
                    )
                    Answer.objects.create(
                        response=response,
                        question=question,
                        value=str(randint(0, 500)),
                        category=None,
                        submitted_on=now(),
                    )
                return True
    except Exception as e:
        print("That failed: %s" % e.args)
        raise
    else:
        return False


class Command(LabelCommand):
    def handle_label(self, label, **options):
        domain = label
        try:
            org = Org.objects.get(subdomain=domain)
        except Org.DoesNotExist:
            print("no such domain: %s" % domain)
            print("valid choices: %s" % Org.objects.values_list('subdomain', flat=True))
        else:
            polls = Poll.objects.filter(org=org, is_active=True)
            if not polls.exists():
                print("That org has no active polls")
            else:
                for poll in polls:
                    # Try faking data for this poll. If successful, done.
                    if try_poll(poll):
                        print("Successfully added data for poll %s" % poll)
                        break
                else:
                    print("Was not able to add data")
