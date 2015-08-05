from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.http import JsonResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect

from dash.orgs.views import OrgPermsMixin
from dash.utils import get_obj_cacheable

from smartmin.users.views import SmartCRUDL, SmartListView, SmartCreateView

from tracpro.contacts.models import Contact
from tracpro.polls.models import PollRun
from .models import Message, InboxMessage
from .forms import InboxMessageResponseForm
from .tasks import send_unsolicited_message, fetch_inbox_messages


class MessageListMixin(object):
    field_config = {
        'text': {'class': 'italicized'},
        'cohort': {'label': _("Recipients")},
        'pollrun': {'label': _("Poll Run")},
    }
    default_order = ('-pk',)
    link_fields = ('pollrun',)

    def get_cohort(self, obj):
        return obj.get_cohort_display()

    def get_region(self, obj):
        return obj.region if obj.region else _("All")

    def lookup_field_link(self, context, field, obj):
        if field == 'pollrun':
            return reverse('polls.pollrun_read', args=[obj.pollrun.pk])

        return super(MessageListMixin, self).lookup_field_link(context, field, obj)


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send', 'by_contact')

    class Send(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            text = request.POST.get('text')
            cohort = request.POST.get('cohort')
            pollrun = PollRun.objects.get(poll__org=org, pk=request.POST.get('pollrun'))
            region = self.request.region

            msg = Message.create(org, self.request.user, text, pollrun, cohort, region)
            return JsonResponse(msg.as_json())

    class List(OrgPermsMixin, MessageListMixin, SmartListView):
        fields = ('sent_on', 'sent_by', 'pollrun', 'cohort', 'region', 'text')
        title = _("Message Log")

        def derive_queryset(self, **kwargs):
            return Message.get_all(self.request.org, self.request.region)

        def lookup_field_link(self, context, field, obj):
            return super(MessageCRUDL.List, self).lookup_field_link(context, field, obj)

    class ByContact(OrgPermsMixin, MessageListMixin, SmartListView):
        fields = ('sent_on', 'sent_by', 'pollrun', 'cohort', 'text')
        field_config = {
            'text': {'class': 'italicized'},
            'cohort': {'label': _("Recipients")},
            'pollrun': {'label': _("Poll Run")},
        }

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<contact>\d+)/$' % (path, action)

        def derive_contact(self):
            def fetch():
                return Contact.objects.get(pk=self.kwargs['contact'], org=self.request.org)
            return get_obj_cacheable(self, '_contact', fetch)

        def derive_queryset(self, **kwargs):
            return self.derive_contact().messages.all()

        def lookup_field_link(self, context, field, obj):
            return super(MessageCRUDL.ByContact, self).lookup_field_link(context, field, obj)

        def get_context_data(self, **kwargs):
            context = super(MessageCRUDL.ByContact, self).get_context_data(**kwargs)
            context['contact'] = self.derive_contact()
            return context


class InboxMessageCRUDL(SmartCRUDL):
    actions = ('read', 'list', 'conversation')
    model = InboxMessage

    class List(OrgPermsMixin, SmartListView):
        fields = ('contact', 'direction', 'text', 'archived', 'created_on', 'delivered_on', 'sent_on')
        link_fields = ('contact', 'text')
        title = "Unsolicited message conversations by most recent message"

        def derive_queryset(self, **kwargs):
            return InboxMessage.get_all(self.request.org).order_by('contact', '-created_on').distinct('contact')

        def lookup_field_link(self, context, field, obj):
            return reverse('msgs.inboxmessage_conversation', kwargs={'contact_id': obj.contact.pk})

    class Conversation(OrgPermsMixin, SmartListView):
        fields = ('text', 'direction', 'created_on')
        title = "Conversation"

        def derive_queryset(self, **kwargs):
            return InboxMessage.get_all(self.request.org).filter(contact=self.contact).order_by('-created_on')

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<contact_id>\d+)/$' % (path, action)

        def dispatch(self, request, contact_id, *args, **kwargs):
            try:
                self.contact = Contact.objects.get(pk=contact_id)
                self.data = self.request.POST or None
            except Contact.DoesNotExist:
                raise Http404("Contact does not exist.")

            self.form = InboxMessageResponseForm(contact=self.contact, data=self.data)

            return super(InboxMessageCRUDL.Conversation, self).dispatch(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super(InboxMessageCRUDL.Conversation, self).get_context_data(**kwargs)
            context['form'] = self.form
            context['contact'] = self.contact
            return context

        def post(self, request, *args, **kwargs):
            form = InboxMessageResponseForm(contact=self.contact, data=request.POST)
            if form.is_valid():
                # Send the new inbox message through the temba task
                send_unsolicited_message.delay(self.request.org, request.POST.get('text'), self.contact)
                # Run the task to pull all inbox messages for this org into the local InboxMessage table
                fetch_inbox_messages(self.request.org)
                return redirect('msgs.inboxmessage_conversation', contact_id=self.contact.pk)
            else:
                return self.get(request, *args, **kwargs)
