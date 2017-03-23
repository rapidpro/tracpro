from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from tracpro.contacts.models import Contact
from tracpro.polls.models import Response

from .tasks import send_message


MESSAGE_MAX_LEN = 640

COHORT_ALL = 'A'
COHORT_RESPONDENTS = 'R'
COHORT_NONRESPONDENTS = 'N'
COHORT_CHOICES = ((COHORT_ALL, _("All participants")),
                  (COHORT_RESPONDENTS, _("Respondents")),
                  (COHORT_NONRESPONDENTS, _("Non-respondents")))

STATUS_PENDING = 'P'
STATUS_SENT = 'S'
STATUS_FAILED = 'F'

STATUS_CHOICES = ((STATUS_PENDING, _("Pending")),
                  (STATUS_SENT, _("Sent")),
                  (STATUS_FAILED, _("Failed")))


@python_2_unicode_compatible
class Message(models.Model):
    """
    Message sent to a cohort associated with an pollrun
    """
    org = models.ForeignKey('orgs.Org', verbose_name=_("Organization"), related_name="messages")

    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="messages")

    sent_on = models.DateTimeField(auto_now_add=True, help_text=_("When the message was sent"))

    text = models.CharField(max_length=MESSAGE_MAX_LEN)

    recipients = models.ManyToManyField(Contact, related_name='messages',
                                        help_text="Contacts to whom this message was sent")

    pollrun = models.ForeignKey('polls.PollRun', null=True, verbose_name=_("Poll Run"), related_name="messages")

    cohort = models.CharField(max_length=1, verbose_name=_("Cohort"), choices=COHORT_CHOICES)

    region = models.ForeignKey('groups.Region', null=True, related_name="messages",
                               verbose_name=_('panel'))

    status = models.CharField(max_length=1, verbose_name=_("Status"), choices=STATUS_CHOICES,
                              help_text=_("Current status of this message"))

    def __str__(self):
        return self.text

    @classmethod
    def create(cls, org, user, text, pollrun, cohort, region):

        message = cls.objects.create(org=org, sent_by=user, text=text, pollrun=pollrun, cohort=cohort, region=region)

        if cohort == COHORT_ALL:
            responses = pollrun.get_responses(region)
        elif cohort == COHORT_RESPONDENTS:
            responses = pollrun.get_responses(region).filter(status=Response.STATUS_COMPLETE)
        elif cohort == COHORT_NONRESPONDENTS:
            responses = pollrun.get_responses(region).exclude(status=Response.STATUS_COMPLETE)
        else:  # pragma: no cover
            raise ValueError("Invalid cohort code: %s" % cohort)

        for contact in [r.contact for r in responses]:
            message.recipients.add(contact)

        send_message.delay(message.pk)

        return message

    @classmethod
    def get_all(cls, org, regions=None):
        messages = cls.objects.filter(org=org)
        if regions is not None:
            # any message to this region or any non-regional message
            messages = messages.filter(Q(region=None) | Q(region__in=regions))
        return messages.select_related('region')

    def as_json(self):
        return dict(id=self.pk, recipients=self.recipients.count())


@python_2_unicode_compatible
class InboxMessage(models.Model):
    """
    Unsolicited Inbox messages sent to RapidPro account
    """
    org = models.ForeignKey("orgs.Org", verbose_name=_("Organization"), related_name="inbox_messages")

    rapidpro_message_id = models.IntegerField()

    contact = models.ForeignKey("contacts.Contact", related_name="inbox_messages")

    text = models.CharField(max_length=MESSAGE_MAX_LEN, null=True)

    archived = models.BooleanField(default=False)

    created_on = models.DateTimeField(null=True)

    delivered_on = models.DateTimeField(null=True)

    sent_on = models.DateTimeField(null=True)

    direction = models.CharField(max_length=1, null=True)

    @classmethod
    def get_all(cls, org, regions=None):
        messages = cls.objects.filter(org=org)
        if regions is not None:
            messages = messages.filter(contact__region__in=regions)
        return messages

    def __str__(self):
        return self.text
