from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
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
        fields = ('sent_on', 'sent_by', 'text', 'issue', 'cohort', 'region')
        field_config = {'cohort': {'label': _("Recipients")}}
        title = _("Message Log")

        def derive_fields(self):
            fields = ['sent_on', 'sent_by', 'text', 'issue', 'cohort']
            if not self.request.region:
                fields.append('region')
            return fields

        def get_queryset(self, **kwargs):
            if self.request.region:
                qs = self.request.region.messages
            else:
                qs = self.request.org.messages
            return qs.order_by('-sent_on')

        def get_cohort(self, obj):
            return obj.get_cohort_display()

    class Send(OrgPermsMixin, SmartCreateView):
        @csrf_exempt
        def dispatch(self, request, *args, **kwargs):
            return super(MessageCRUDL.Send, self).dispatch(request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            text = request.POST.get('text')
            cohort = request.POST.get('cohort')
            issue = Issue.objects.get(poll__org=org, pk=request.POST.get('issue'))
            region = self.request.region

            msg = Message.create(org, self.request.user, text, issue, cohort, region)
            return JsonResponse(msg.as_json())
