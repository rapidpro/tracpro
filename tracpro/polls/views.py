from __future__ import absolute_import, unicode_literals

from collections import OrderedDict
from itertools import chain

import unicodecsv

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import datetime_to_ms, get_obj_cacheable

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse)
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from smartmin import views as smartmin
from smartmin.templatetags.smartmin import format_datetime

from tracpro.contacts.models import Contact
from tracpro.groups.models import Group, Region

from . import charts, forms, tasks
from .models import Poll, Question, PollRun, Response, Window


class PollCRUDL(smartmin.SmartCRUDL):
    model = Poll
    actions = ('read', 'update', 'list', 'select')

    class PollMixin(object):

        def get_queryset(self):
            """Only allow viewing active polls for the current org."""
            return Poll.get_all(self.request.org)

    class Read(PollMixin, OrgObjPermsMixin, smartmin.SmartReadView):

        def get_context_data(self, **kwargs):
            context = super(PollCRUDL.Read, self).get_context_data(**kwargs)
            questions = self.object.get_questions()
            pollruns = self.object.get_pollruns(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

            # if we're viewing "All Regions" don't include regional only pollruns
            if not self.request.region:
                pollruns = pollruns.universal()

            window = self.request.POST.get('window', self.request.GET.get('window', None))
            window = Window[window] if window else Window.last_30_days
            window_min, window_max = window.to_range()

            pollruns = pollruns.filter(conducted_on__gte=window_min, conducted_on__lt=window_max)
            pollruns = pollruns.order_by('conducted_on')

            for question in questions:
                question.chart_type, question.chart_data = charts.multiple_pollruns(
                    pollruns, question, self.request.data_regions)

            context['window'] = window
            context['window_min'] = datetime_to_ms(window_min)
            context['window_max'] = datetime_to_ms(window_max)
            context['window_options'] = Window.__members__.values()
            context['questions'] = questions
            return context

    class Update(PollMixin, OrgObjPermsMixin, smartmin.SmartUpdateView):
        exclude = ('is_active', 'flow_uuid', 'org')
        form_class = forms.PollForm

        def post_save(self, obj):
            for field_key, value in self.form.cleaned_data.iteritems():
                if field_key.startswith('__question__'):
                    question_id = field_key.split('__')[2]
                    Question.objects.filter(pk=question_id, poll=self.object).update(text=value)

    class List(PollMixin, OrgPermsMixin, smartmin.SmartListView):
        fields = ('name', 'questions', 'pollruns', 'last_conducted')
        field_config = {'pollruns': {'label': _("Dates")}}
        link_fields = ('name', 'pollruns')
        default_order = ('name',)

        def derive_pollruns(self, obj):
            return obj.get_pollruns(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

        def get_questions(self, obj):
            return obj.get_questions().count()

        def get_pollruns(self, obj):
            return self.derive_pollruns(obj).count()

        def get_last_conducted(self, obj):
            last_pollrun = self.derive_pollruns(obj).order_by('-conducted_on').first()
            return last_pollrun.conducted_on if last_pollrun else _("Never")

        def lookup_field_link(self, context, field, obj):
            if field == 'pollruns':
                return reverse('polls.pollrun_by_poll', args=[obj.pk])

            return super(PollCRUDL.List, self).lookup_field_link(context, field, obj)

    class Select(OrgPermsMixin, smartmin.SmartFormView):
        title = _("Poll Flows")
        form_class = forms.FlowsForm
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


class PollRunListMixin(object):
    default_order = ('-conducted_on',)

    def get_conducted_on(self, obj):
        return obj.conducted_on.strftime(settings.SITE_DATE_FORMAT)

    def get_participants(self, obj):
        def calculate():
            return obj.get_response_counts(
                self.request.region, self.request.include_subregions)
        counts = get_obj_cacheable(obj, '_response_counts', calculate)
        return chain(counts.values())

    def get_responses(self, obj):
        def calculate():
            return obj.get_response_counts(
                self.request.region, self.request.include_subregions)
        counts = get_obj_cacheable(obj, '_response_counts', calculate)
        if counts[Response.STATUS_PARTIAL]:
            return "{complete} ({partial})".format(
                complete=counts[Response.STATUS_COMPLETE],
                partial=counts[Response.STATUS_PARTIAL],
            )
        else:
            return counts[Response.STATUS_COMPLETE]

    def get_region(self, obj):
        return obj.region.name if obj.region else _("All")

    def lookup_field_link(self, context, field, obj):
        if field == 'poll':
            return reverse('polls.poll_read', args=[obj.poll_id])
        if field == 'conducted_on':
            return reverse('polls.pollrun_read', args=[obj.pk])
        elif field == 'participants':
            return reverse('polls.pollrun_participation', args=[obj.pk])
        elif field == 'responses':
            return reverse('polls.response_by_pollrun', args=[obj.pk])


class PollRunCRUDL(smartmin.SmartCRUDL):
    model = PollRun
    actions = (
        'create', 'restart', 'read', 'participation', 'list', 'by_poll',
        'latest')

    class Create(OrgPermsMixin, smartmin.SmartCreateView):

        def post(self, request, *args, **kwargs):
            try:
                poll = Poll.get_all(self.request.org).get(pk=request.POST.get('poll'))
            except Poll.DoesNotExist:
                return HttpResponseBadRequest()

            kwargs = {
                'region': request.region,
                'poll': poll,
                'created_by': self.request.user,
            }

            # Note: This is separate from the include_subregions session
            # setting.
            if request.POST.get('propagate', False):
                pollrun = PollRun.objects.create_propagated(**kwargs)
            else:
                pollrun = PollRun.objects.create_regional(**kwargs)

            return JsonResponse(pollrun.as_json(
                request.region, self.request.include_subregions))

    class Restart(OrgPermsMixin, smartmin.SmartFormView):

        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            pollrun = PollRun.objects.by_org(org).get(
                pk=request.POST.get('pollrun'))
            region = request.region

            incomplete_responses = pollrun.get_incomplete_responses(region)
            contact_uuids = [r.contact.uuid for r in incomplete_responses]

            tasks.pollrun_restart_participants.delay(pollrun.pk, contact_uuids)

            return JsonResponse({'contacts': len(contact_uuids)})

    class Read(OrgPermsMixin, smartmin.SmartReadView):

        def get_queryset(self):
            return PollRun.objects.get_all(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

        def get_context_data(self, **kwargs):
            context = super(PollRunCRUDL.Read, self).get_context_data(**kwargs)
            questions = self.object.poll.get_questions()

            for question in questions:
                question.chart_type, question.chart_data = charts.single_pollrun(
                    self.object, question, self.request.data_regions)

            context['questions'] = questions
            return context

    class Participation(OrgPermsMixin, smartmin.SmartReadView):

        def get_queryset(self):
            return PollRun.objects.get_all(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

        def get_context_data(self, **kwargs):
            context = super(PollRunCRUDL.Participation, self).get_context_data(**kwargs)
            responses = self.object.get_responses(
                self.request.region,
                self.request.include_subregions)
            group_by = self.request.GET.get('group-by', 'reporter')
            if group_by == "reporter":
                group_by_reporter_group = True
                groups_or_regions = Group.get_all(self.request.org).order_by('name')
            else:
                group_by_reporter_group = False
                if self.request.data_regions:
                    groups_or_regions = self.request.data_regions
                else:
                    groups_or_regions = Region.objects.filter(org=self.request.org)

            # initialize an ordered dict of group to response counts
            per_group_counts = OrderedDict()
            no_group_counts = {'E': 0, 'P': 0, 'C': 0}
            overall_counts = {'E': 0, 'P': 0, 'C': 0}

            # Calculate all reporter group or region activity per group or region
            for group_or_region in groups_or_regions:
                if group_by_reporter_group:
                    responses_group = responses.filter(contact__group=group_or_region)
                else:
                    responses_group = responses.filter(contact__region=group_or_region)
                if responses_group:
                    per_group_counts[group_or_region] = {
                        "E": responses_group.filter(status=Response.STATUS_EMPTY).count(),
                        "P": responses_group.filter(status=Response.STATUS_PARTIAL).count(),
                        "C": responses_group.filter(status=Response.STATUS_COMPLETE).count()
                    }
                    overall_counts['E'] = overall_counts['E'] + per_group_counts[group_or_region]['E']
                    overall_counts['P'] = overall_counts['P'] + per_group_counts[group_or_region]['P']
                    overall_counts['C'] = overall_counts['C'] + per_group_counts[group_or_region]['C']
                else:
                    per_group_counts[group_or_region] = {'E': 0, 'P': 0, 'C': 0}
            # Calculate all no-group or no-region activity
            if group_by_reporter_group:
                responses_no_group = responses.filter(contact__group__isnull=True)
            else:
                responses_no_group = responses.filter(contact__region__isnull=True)
            if responses_no_group:
                no_group_counts = {
                    "E": responses_no_group.filter(status=Response.STATUS_EMPTY).count(),
                    "P": responses_no_group.filter(status=Response.STATUS_PARTIAL).count(),
                    "C": responses_no_group.filter(status=Response.STATUS_COMPLETE).count()
                }
                overall_counts['E'] = overall_counts['E'] + no_group_counts['E']
                overall_counts['P'] = overall_counts['P'] + no_group_counts['P']
                overall_counts['C'] = overall_counts['C'] + no_group_counts['C']

            def calc_completion(counts):
                total = counts['E'] + counts['P'] + counts['C']
                return "%d%%" % int(100 * counts['C'] / total) if total else ''

            # for each set of counts, also calculate the completion percentage
            for group, counts in per_group_counts.iteritems():
                counts['X'] = calc_completion(counts)

            no_group_counts['X'] = calc_completion(no_group_counts)
            overall_counts['X'] = calc_completion(overall_counts)

            # participation table counts
            context['per_group_counts'] = per_group_counts
            context['no_group_counts'] = no_group_counts
            context['overall_counts'] = overall_counts

            # message recipient counts
            context['all_participants_count'] = sum((
                overall_counts['E'],
                overall_counts['P'],
                overall_counts['C'],
            ))
            context['incomplete_count'] = sum((
                overall_counts['E'],
                overall_counts['P'],
            ))
            context['complete_count'] = overall_counts['C']
            context['group_by_reporter_group'] = group_by_reporter_group
            return context

    class List(OrgPermsMixin, PollRunListMixin, smartmin.SmartListView):
        """
        All pollruns in current region
        """
        fields = ('conducted_on', 'poll', 'region', 'participants', 'responses')
        link_fields = ('conducted_on', 'poll', 'participants', 'responses')
        add_button = False

        def derive_title(self):
            return _("All Poll Runs")

        def derive_queryset(self, **kwargs):
            return PollRun.objects.get_all(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

    class ByPoll(OrgPermsMixin, PollRunListMixin, smartmin.SmartListView):
        """
        Poll Runs filtered by poll
        """
        fields = ('conducted_on', 'region', 'participants', 'responses')
        link_fields = ('conducted_on', 'participants', 'responses')

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<poll>\d+)/$' % (path, action)

        def derive_poll(self):
            def fetch():
                poll_qs = Poll.get_all(self.request.org)
                return get_object_or_404(poll_qs, pk=self.kwargs['poll'])
            return get_obj_cacheable(self, '_poll', fetch)

        def derive_queryset(self, **kwargs):
            return self.derive_poll().get_pollruns(
                self.request.org,
                self.request.region,
                self.request.include_subregions)

        def get_context_data(self, **kwargs):
            context = super(PollRunCRUDL.ByPoll, self).get_context_data(**kwargs)
            context['poll'] = self.derive_poll()
            return context

    class Latest(OrgPermsMixin, smartmin.SmartListView):

        def get_queryset(self):
            qs = PollRun.objects.get_all(
                self.request.org,
                self.request.region,
                self.request.include_subregions)
            qs = qs.order_by('-conducted_on')[0:5]
            return qs

        def render_to_response(self, context, **response_kwargs):
            results = [i.as_json(self.request.region, self.request.include_subregions)
                       for i in context['object_list']]
            return JsonResponse({'count': len(results), 'results': results})


class ResponseCRUDL(smartmin.SmartCRUDL):
    model = Response
    actions = ('by_pollrun', 'by_contact')

    class ByPollrun(OrgPermsMixin, smartmin.SmartListView):
        default_order = ('-updated_on',)
        field_config = {'updated_on': {'label': _("Date")}}
        link_fields = ('contact',)

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<pollrun>\d+)/$' % (path, action)

        def derive_pollrun(self):
            def fetch():
                pollrun_qs = PollRun.objects.by_org(self.request.org)
                pollrun_qs = pollrun_qs.select_related('poll')
                return get_object_or_404(pollrun_qs, pk=self.kwargs['pollrun'])
            return get_obj_cacheable(self, '_pollrun', fetch)

        def derive_questions(self):
            def fetch():
                questions = OrderedDict()
                for question in self.derive_pollrun().poll.get_questions():
                    questions['question_%d' % question.pk] = question
                return questions

            return get_obj_cacheable(self, '_questions', fetch)

        def derive_fields(self):
            base_fields = ['updated_on', 'contact', 'region', 'group']
            return base_fields + self.derive_questions().keys()

        def derive_queryset(self, **kwargs):
            # only show partial and complete responses
            return self.derive_pollrun().get_responses(
                region=self.request.region,
                include_subregions=self.request.include_subregions,
                include_empty=False)

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('question_'):
                question = self.derive_questions()[field]
                return question.text
            else:
                return super(ResponseCRUDL.ByPollrun, self).lookup_field_label(
                    context, field, default)

        def lookup_field_value(self, context, obj, field):
            if field == 'region':
                return obj.contact.region
            elif field == 'group':
                return obj.contact.group
            elif field.startswith('question_'):
                question = self.derive_questions()[field]
                answer = obj.answers.filter(question=question).first()
                if answer:
                    if question.type == Question.TYPE_RECORDING:
                        return '<a class="answer answer-audio" href="%s" data-answer-id="%d">Play</a>' % (
                            answer.value,
                            answer.pk,
                        )
                    else:
                        return answer.value
                else:
                    return '--'
            else:
                return super(ResponseCRUDL.ByPollrun, self).lookup_field_value(
                    context, obj, field)

        def lookup_field_link(self, context, field, obj):
            if field == 'contact':
                return reverse('contacts.contact_read', args=[obj.contact.pk])

            return super(ResponseCRUDL.ByPollrun, self).lookup_field_link(
                context, field, obj)

        def get_context_data(self, **kwargs):
            context = super(ResponseCRUDL.ByPollrun, self).get_context_data(**kwargs)
            pollrun = self.derive_pollrun()
            context['pollrun'] = pollrun

            if '_format' not in self.request.POST and '_format' not in self.request.GET:
                # can only restart regional polls and if they're the last pollrun
                can_restart = self.request.region and pollrun.is_last_for_region(
                    self.request.region)

                counts = pollrun.get_response_counts(
                    self.request.region, self.request.include_subregions)

                context['can_restart'] = can_restart
                context['response_count'] = sum([
                    counts[Response.STATUS_EMPTY],
                    counts[Response.STATUS_PARTIAL],
                    counts[Response.STATUS_COMPLETE],
                ])
                context['complete_response_count'] = counts[Response.STATUS_COMPLETE]
                context['incomplete_response_count'] = sum([
                    counts[Response.STATUS_EMPTY],
                    counts[Response.STATUS_PARTIAL],
                ])
            return context

        def render_to_response(self, context, **response_kwargs):
            _format = self.request.POST.get('_format', self.request.GET.get('_format', None))

            if _format == 'csv':
                response = HttpResponse(content_type='text/csv', status=200)
                response['Content-Disposition'] = 'attachment; filename="responses.csv"'
                writer = unicodecsv.writer(response)

                questions = self.derive_questions().values()

                resp_headers = ['Date']
                contact_headers = ['Name', 'URN', 'Region', 'Group']
                question_headers = [q.text for q in questions]
                writer.writerow(resp_headers + contact_headers + question_headers)

                for resp in context['object_list']:
                    resp_cols = [format_datetime(resp.updated_on)]
                    contact_cols = [
                        resp.contact.name, resp.contact.urn,
                        resp.contact.region, resp.contact.group]
                    answer_cols = []

                    answers_by_question_id = {a.question_id: a for a in resp.answers.all()}
                    for question in questions:
                        answer = answers_by_question_id.get(question.pk, None)
                        answer_cols.append(answer.value if answer else '')

                    writer.writerow(resp_cols + contact_cols + answer_cols)

                return response
            else:
                return super(ResponseCRUDL.ByPollrun, self).render_to_response(
                    context, **response_kwargs)

    class ByContact(OrgPermsMixin, smartmin.SmartListView):
        fields = ('updated_on', 'poll', 'answers')
        field_config = {'updated_on': {'label': _("Date")}}
        link_fields = ('updated_on', 'poll')
        default_order = ('-updated_on',)

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<contact>\d+)/$' % (path, action)

        def derive_contact(self):
            def fetch():
                contact_qs = Contact.objects.filter(org=self.request.org)
                contact_qs = contact_qs.select_related('region')
                return get_object_or_404(contact_qs, pk=self.kwargs['contact'])
            return get_obj_cacheable(self, '_contact', fetch)

        def derive_queryset(self, **kwargs):
            qs = self.derive_contact().get_responses(include_empty=True)

            return qs.select_related('pollrun__poll').prefetch_related('answers')

        def get_poll(self, obj):
            return obj.pollrun.poll

        def get_answers(self, obj):
            answers_by_q_id = {a.question_id: a for a in obj.answers.all()}
            answers = []

            if not answers_by_q_id:
                return '<i>%s</i>' % _("No response")

            questions = obj.pollrun.poll.get_questions()
            for question in questions:
                answer = answers_by_q_id.get(question.pk, None)
                if not answer:
                    answer_display = ""
                elif question.type == Question.TYPE_OPEN:
                    answer_display = answer.value
                else:
                    answer_display = answer.category

                answers.append("%d. %s: <em>%s</em>" % (question.order, question.text, answer_display))

            return "<br/>".join(answers)

        def lookup_field_link(self, context, field, obj):
            if field == 'updated_on':
                return reverse('polls.pollrun_read', args=[obj.pollrun_id])
            elif field == 'poll':
                return reverse('polls.poll_read', args=[obj.pollrun.poll_id])

        def get_context_data(self, **kwargs):
            context = super(ResponseCRUDL.ByContact, self).get_context_data(**kwargs)
            context['contact'] = self.derive_contact()
            return context
