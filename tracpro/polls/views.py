from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartCRUDL, SmartListView, SmartFormView
from .models import Poll


class PollCRUDL(SmartCRUDL):
    model = Poll
    actions = ('list', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name',)

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()
            return Poll.get_all(org).order_by('name')

    class Select(OrgPermsMixin, SmartFormView):
        class FlowsForm(forms.Form):
            flows = forms.MultipleChoiceField(choices=(), label=_("Flows"), help_text=_("Flows to track as polls."))

            def __init__(self, *args, **kwargs):
                org = kwargs.pop('org')

                super(PollCRUDL.Select.FlowsForm, self).__init__(*args, **kwargs)

                choices = []
                for flow in org.get_temba_client().get_flows():
                    choices.append((flow.uuid, flow.name))

                self.fields['flows'].choices = choices
                self.fields['flows'].initial = Poll.get_all(org).order_by('name')

        title = _("Poll Flows")
        form_class = FlowsForm
        success_url = '@polls.poll_list'
        submit_button_name = _("Update")
        success_message = _("Updated flows to track as polls")

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Select, self).get_form_kwargs()
            kwargs['org'] = self.request.org
            return kwargs

        def form_valid(self, form):
            Poll.update_flows(self.request.org, form.cleaned_data['flows'])
            return HttpResponseRedirect(self.get_success_url())