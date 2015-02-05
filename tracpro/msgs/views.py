from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from smartmin.users.views import SmartCRUDL, SmartListView, SmartCreateView
from tracpro.polls.models import Issue
from .models import Message


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send')

    class List(OrgPermsMixin, SmartListView):
        fields = ('sent_on', 'sent_by', 'issue', 'cohort', 'region', 'text')
        field_config = {'text': {'class': 'italicized'},
                        'cohort': {'label': _("Recipients")},
                        'issue': {'label': _("Poll")}}
        title = _("Message Log")
        default_order = ('-sent_on',)

        def derive_fields(self):
            fields = ['sent_on', 'sent_by', 'text', 'issue', 'cohort']
            if not self.request.region:
                fields.append('region')
            return fields

        def derive_link_fields(self, context):
            return ('issue',)

        def derive_queryset(self, **kwargs):
            if self.request.region:
                return self.request.region.messages.all()
            else:
                return self.request.org.messages.all()

        def get_cohort(self, obj):
            return obj.get_cohort_display()

        def lookup_field_link(self, context, field, obj):
            if field == 'issue':
                return reverse('polls.response_filter', args=[obj.pk])

            return super(MessageCRUDL.List, self).lookup_field_link(context, field, obj)

    class Send(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            text = request.POST.get('text')
            cohort = request.POST.get('cohort')
            issue = Issue.objects.get(poll__org=org, pk=request.POST.get('issue'))
            region = self.request.region

            msg = Message.create(org, self.request.user, text, issue, cohort, region)
            return JsonResponse(msg.as_json())
