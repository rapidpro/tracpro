from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartCRUDL, SmartListView, SmartFormView
from .models import Poll, Question


class PollCRUDL(SmartCRUDL):
    model = Poll
    actions = ('list', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'questions', 'last_conducted')

        def derive_link_fields(self, context):
            return 'name',

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()
            return Poll.get_all(org).order_by('name')

        def get_questions(self, obj):
            return obj.get_questions().count()

        def get_last_conducted(self, obj):
            last_issue = obj.issues.order_by('-conducted_on').first()
            return last_issue.conducted_on if last_issue else _("Never")

        def lookup_field_link(self, context, field, obj):
            return reverse('polls.question_filter', kwargs=dict(poll=obj.pk))

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


class QuestionCRUDL(SmartCRUDL):
    model = Question
    actions = ('filter',)

    class Filter(OrgPermsMixin, SmartListView):
        fields = ('text', 'show_with_contact')

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<poll>\d+)/$' % (path, action)

        def derive_title(self):
            return _("Questions in %s") % self.derive_poll().name

        def derive_poll(self):
            if hasattr(self, '_poll'):
                return self._poll

            self._poll = Poll.objects.get(pk=self.kwargs['poll'], org=self.request.org)
            return self._poll

        def get_queryset(self, **kwargs):
            return self.derive_poll().get_questions().order_by('pk')

        def get_context_data(self, **kwargs):
            context = super(QuestionCRUDL.Filter, self).get_context_data(**kwargs)
            context['poll'] = self.derive_poll()
            return context