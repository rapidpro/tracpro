from __future__ import absolute_import, unicode_literals

import json

from collections import OrderedDict, Counter
from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartCRUDL, SmartCreateView, SmartReadView, SmartListView, SmartFormView
from .models import Poll, Issue, Response, RESPONSE_EMPTY, RESPONSE_PARTIAL, RESPONSE_COMPLETE
from .tasks import issue_restart_participants


class PollCRUDL(SmartCRUDL):
    model = Poll
    actions = ('read', 'list', 'select')

    class Read(OrgObjPermsMixin, SmartReadView):
        fields = ('name', 'questions', 'issues', 'last_conducted')

        def derive_issues(self, obj):
            return Issue.get_all(self.request.org, self.request.region, poll=obj)

        def get_questions(self, obj):
            return "<br/>".join([q.text for q in obj.get_questions()])

        def get_issues(self, obj):
            return self.derive_issues(obj).count()

        def get_last_conducted(self, obj):
            last_issue = self.derive_issues(obj).order_by('-conducted_on').first()
            return last_issue.conducted_on if last_issue else _("Never")

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'questions', 'issues', 'last_conducted')
        default_order = ('name',)

        def derive_queryset(self, **kwargs):
            return Poll.get_all(self.request.org)

        def derive_issues(self, obj):
            return Issue.get_all(self.request.org, self.request.region, poll=obj)

        def get_questions(self, obj):
            return obj.get_questions().count()

        def get_issues(self, obj):
            return self.derive_issues(obj).count()

        def get_last_conducted(self, obj):
            last_issue = self.derive_issues(obj).order_by('-conducted_on').first()
            return last_issue.conducted_on if last_issue else _("Never")

    class Select(OrgPermsMixin, SmartFormView):
        class FlowsForm(forms.Form):
            flows = forms.MultipleChoiceField(choices=(), label=_("Flows"), help_text=_("Flows to track as polls."))

            def __init__(self, *args, **kwargs):
                org = kwargs.pop('org')

                super(PollCRUDL.Select.FlowsForm, self).__init__(*args, **kwargs)

                choices = []
                for flow in org.get_temba_client().get_flows(archived=False):
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
            Poll.sync_with_flows(self.request.org, form.cleaned_data['flows'])
            return HttpResponseRedirect(self.get_success_url())


class IssueCRUDL(SmartCRUDL):
    model = Issue
    actions = ('read', 'list', 'latest', 'start', 'restart')

    class Read(OrgPermsMixin, SmartReadView):
        def get_queryset(self):
            return Issue.get_all(self.request.org, self.request.region)

        def get_context_data(self, **kwargs):
            context = super(IssueCRUDL.Read, self).get_context_data(**kwargs)

            response_counts = self.object.get_response_counts(self.request.region)
            questions = self.object.poll.get_questions()

            for question in questions:
                answers = self.object.get_answers_to(question)
                category_counts = Counter([answer.category for answer in answers])

                # TODO what to do for questions that are open-ended
                # is_open_ended = len(category_counts.keys()) == 1

                data = [[category, count] for category, count in category_counts.iteritems()]
                question.chart_data = mark_safe(json.dumps(data))

            context['response_counts'] = response_counts
            context['questions'] = questions
            return context

    class List(OrgPermsMixin, SmartListView):
        """
        All issues in current region
        """
        fields = ('poll', 'conducted_on', 'region', 'responses')
        default_order = ('-conducted_on',)

        def derive_title(self):
            return _("All Polls")

        def derive_link_fields(self, context):
            return 'poll', 'conducted_on', 'responses'

        def derive_queryset(self, **kwargs):
            return Issue.get_all(self.request.org, self.request.region)

        def get_responses(self, obj):
            counts = obj.get_response_counts(self.request.region)
            total = counts[RESPONSE_EMPTY] + counts[RESPONSE_PARTIAL] + counts[RESPONSE_COMPLETE]
            return "%d / %d" % (counts[RESPONSE_COMPLETE], total)

        def get_region(self, obj):
            return obj.region if obj.region else _("All")

        def lookup_field_link(self, context, field, obj):
            if field == 'poll':
                return reverse('polls.poll_read', args=[obj.poll_id])
            elif field == 'conducted_on':
                return reverse('polls.issue_read', args=[obj.pk])
            elif field == 'responses':
                return reverse('polls.response_filter', kwargs=dict(issue=obj.pk))

    class Latest(OrgPermsMixin, SmartListView):
        def get_queryset(self):
            return Issue.get_all(self.request.org, self.request.region).order_by('-conducted_on')[0:5]

        def render_to_response(self, context, **response_kwargs):
            results = [i.as_json(self.request.region) for i in context['object_list']]
            return JsonResponse({'count': len(results), 'results': results})

    class Start(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            poll = Poll.objects.get(org=org, pk=request.POST.get('poll'))
            issue = Issue.create(poll, request.region, timezone.now(), do_start=True)
            return JsonResponse(issue.as_json(request.region))

    class Restart(OrgPermsMixin, SmartFormView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            issue = Issue.objects.get(poll__org=org, pk=request.POST.get('issue'))
            region = request.region

            incomplete_responses = issue.get_incomplete_responses(region)
            contact_uuids = [r.contact.uuid for r in incomplete_responses]

            issue_restart_participants.delay(issue.pk, contact_uuids)

            return JsonResponse({'contacts': len(contact_uuids)})


class ResponseCRUDL(SmartCRUDL):
    model = Response
    actions = ('filter',)

    class Filter(OrgPermsMixin, SmartListView):
        default_order = ('-created_on',)

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<issue>\d+)/$' % (path, action)

        def derive_title(self):
            return unicode(self.derive_issue())

        def derive_issue(self):
            if hasattr(self, '_issue'):
                return self._issue

            self._issue = Issue.objects.select_related('poll').get(pk=self.kwargs['issue'], poll__org=self.request.org)
            return self._issue

        def derive_questions(self):
            if hasattr(self, '_questions'):
                return self._questions

            self._questions = OrderedDict()
            for question in self.derive_issue().poll.get_questions():
                self._questions['question_%d' % question.pk] = question
            return self._questions

        def derive_fields(self):
            base_fields = ['created_on', 'contact']
            if not self.request.region:
                base_fields.append('region')
            return base_fields + ['group'] + self.derive_questions().keys()

        def derive_link_fields(self, context):
            return 'contact',

        def derive_queryset(self, **kwargs):
            return self.derive_issue().get_responses(region=self.request.region)

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('question_'):
                question = self.derive_questions()[field]
                return question.text
            else:
                return super(ResponseCRUDL.Filter, self).lookup_field_label(context, field, default)

        def lookup_field_value(self, context, obj, field):
            if field == 'region':
                return obj.contact.region
            elif field == 'group':
                return obj.contact.group
            elif field.startswith('question_'):
                question = self.derive_questions()[field]
                answer = obj.answers.filter(question=question).first()
                return answer.value if answer else '--'
            else:
                return super(ResponseCRUDL.Filter, self).lookup_field_value(context, obj, field)

        def lookup_field_link(self, context, field, obj):
            if field == 'contact':
                return reverse('contacts.contact_read', args=[obj.contact.pk])

            return super(ResponseCRUDL.Filter, self).lookup_field_link(context, field, obj)

        def get_context_data(self, **kwargs):
            context = super(ResponseCRUDL.Filter, self).get_context_data(**kwargs)
            issue = self.derive_issue()

            # can only restart regional polls and if they're the last issue
            can_restart = self.request.region and issue.is_last_for_region(self.request.region)

            counts = issue.get_response_counts(self.request.region)

            context['issue'] = issue
            context['can_restart'] = can_restart
            context['response_count'] = counts[RESPONSE_EMPTY] + counts[RESPONSE_PARTIAL] + counts[RESPONSE_COMPLETE]
            context['complete_response_count'] = counts[RESPONSE_COMPLETE]
            context['incomplete_response_count'] = counts[RESPONSE_EMPTY] + counts[RESPONSE_PARTIAL]
            return context