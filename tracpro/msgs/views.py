from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartListView, SmartCreateView
from tracpro.polls.models import Issue
from .models import Message


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send')

    class List(OrgPermsMixin, SmartListView):
        fields = ('time', 'user', 'text', 'issue', 'cohort', 'region')
        title = _("Message Log")

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()
            return org.messages.order_by('-time')

    class Send(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            text = request.REQUEST.get('text')
            issue = Issue.objects.get(poll__org=org, pk=request.REQUEST.get('issue'))
            cohort = request.REQUEST.get('cohort')
            region = self.request.region

            msg = Message.create(org, self.request.user, text, issue, cohort, region)
            return JsonResponse(msg.as_json())
