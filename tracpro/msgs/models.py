from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from tracpro.contacts.models import Contact
from tracpro.groups.models import Region
from tracpro.polls.models import Issue
from .tasks import send_message

MESSAGE_MAX_LEN = 640

COHORT_ALL = 'A'
COHORT_RESPONDENTS = 'R'
COHORT_NONRESPONDENTS = 'N'
COHORT_CHOICES = ((COHORT_ALL, _("All")),
                  (COHORT_RESPONDENTS, _("Respondents")),
                  (COHORT_NONRESPONDENTS, _("Non-respondents")))

STATUS_PENDING = 'P'
STATUS_SENT = 'S'
STATUS_FAILED = 'F'

STATUS_CHOICES = ((STATUS_PENDING, _("Pending")),
                  (STATUS_SENT, _("Sent")),
                  (STATUS_FAILED, _("Failed")))


class Message(models.Model):
    """
    Message sent to a cohort associated with an issue
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name="messages")

    user = models.ForeignKey(User, verbose_name=_("Sender"), related_name="messages")

    text = models.CharField(max_length=MESSAGE_MAX_LEN)

    recipients = models.ManyToManyField(Contact, related_name='messages',
                                        help_text="Contacts to whom this message was sent")

    time = models.DateTimeField(auto_now_add=True, help_text=_("When the message was sent"))

    issue = models.ForeignKey(Issue, verbose_name=_("Poll Issue"), related_name="messages")

    cohort = models.CharField(max_length=1, verbose_name=_("Cohort"), choices=COHORT_CHOICES)

    region = models.ForeignKey(Region)

    status = models.CharField(max_length=1, verbose_name=_("Status"), choices=STATUS_CHOICES,
                              help_text=_("Current status of this message"))

    @classmethod
    def create(cls, org, user, text, issue, cohort, region):
        message = cls.objects.create(org=org, user=user, text=text, issue=issue, cohort=cohort, region=region)

        if cohort == COHORT_ALL:
            responses = issue.get_responses(region)
        elif cohort == COHORT_RESPONDENTS:
            responses = issue.get_complete_responses(region)
        elif cohort == COHORT_NONRESPONDENTS:
            responses = issue.get_incomplete_responses(region)
        else:
            raise ValueError("Invalid cohort code: %s" % cohort)

        for contact in [r.contact for r in responses]:
            message.recipients.add(contact)

        send_message.delay(message.pk)

        return message

    def as_json(self):
        return dict(id=self.pk,
                    user_id=self.user.pk,
                    text=self.text,
                    time=self.time,
                    issue_id=self.issue.pk,
                    cohort=self.cohort,
                    region_id=self.region.pk)
