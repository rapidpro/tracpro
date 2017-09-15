from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import unicodecsv

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import get_obj_cacheable

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseBadRequest, JsonResponse)
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from smartmin import views as smartmin
from smartmin.templatetags.smartmin import format_datetime

from tracpro.contacts.models import Contact
from tracpro.groups.models import Group, Region

from . import charts, forms, maps, tasks
from .models import Poll, Question, PollRun, Response


class PollCRUDL(smartmin.SmartCRUDL):
    model = Poll
    actions = ('read', 'update', 'list', 'select')

    class PollMixin(object):

        def get_queryset(self):
            """Only allow viewing active polls for the current org."""
            return Poll.objects.active().by_org(self.request.org)

    class Read(PollMixin, OrgObjPermsMixin, smartmin.SmartReadView):

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()
            self.filter_form = forms.PollChartFilterForm(
                org=self.object.org, data=request.GET)
            return self.render_to_response(self.get_context_data(
                object=self.object,
                form=self.filter_form,
                question_data=self.get_question_data(),
            ))

        def get_pollruns(self):
            """The x-axis of each chart shows the PollRun date."""
            pollruns = self.object.pollruns.active()

            # Limit pollrun dates.
            start_date = self.filter_form.cleaned_data.get('start_date')
            end_date = self.filter_form.cleaned_data.get('end_date')
            pollruns = pollruns.by_dates(start_date, end_date)

            if self.request.region:
                # Show only pollruns conducted in the region.
                pollruns = pollruns.by_region(
                    self.request.region,
                    self.request.include_subregions)
            else:
                # Show only non-regional pollruns.
                pollruns = pollruns.universal()

            return pollruns

        def get_responses(self, pollruns):
            """Limit the responses from which data is shown."""
            contacts = Contact.objects.filter(org=self.request.org)
            contacts = contacts.filter(
                region__is_active=True,
                is_active=True)  # Filter out inactive contacts
            contacts = self.filter_form.filter_contacts(contacts)

            if self.request.region:
                contacts = contacts.filter(region__in=self.request.data_regions)

            responses = Response.objects.active()
            responses = responses.filter(contact__in=contacts)
            responses = responses.filter(pollrun__in=pollruns)
            return responses

        def get_question_data(self):
            # Do not display any data if invalid data was submitted.
            if not self.filter_form.is_valid():
                return None

            pollruns = self.get_pollruns()
            responses = self.get_responses(pollruns)
            split_regions = self.filter_form.cleaned_data['split_regions']
            # Get the contact fields so we can pass them to the pollrun url
            contact_filters = {}
            for fieldname in self.filter_form.fields:
                if fieldname.startswith('contact'):
                    contact_filters[fieldname] = self.filter_form.cleaned_data[fieldname]

            data = []
            for question in self.object.questions.active():
                chart_type, chart_data, summary_table = charts.multiple_pollruns(
                    pollruns, responses, question, split_regions, contact_filters)
                map_data = maps.get_map_data(responses, question)
                data.append((
                    question,
                    chart_type,
                    chart_data,
                    map_data,
                    summary_table,
                ))
            return data

    class Update(PollMixin, OrgObjPermsMixin, smartmin.SmartUpdateView):
        form_class = forms.PollForm
        formset_class = forms.QuestionFormSet
        success_url = 'id@polls.poll_read'

        def dispatch(self, *args, **kwargs):
            self.object = self.get_object()
            self.form = self.get_form()
            self.formset = self.get_formset()
            return super(PollCRUDL.Update, self).dispatch(*args, **kwargs)

        def form_invalid(self, form, formset):
            return self.render_to_response(self.get_context_data())

        def form_valid(self, form, formset):
            self.object = form.save()
            formset.save()
            messages.success(self.request, self.derive_success_message())
            return redirect(self.get_success_url())

        def get_context_data(self, **kwargs):
            kwargs.setdefault('object', self.object)
            kwargs.setdefault('form', self.form)
            kwargs.setdefault('questions_formset', self.formset)
            return super(PollCRUDL.Update, self).get_context_data(**kwargs)

        def get_formset(self):
            questions = self.object.questions.all()
            data = self.request.POST if self.request.method == 'POST' else None
            return self.formset_class(data=data, queryset=questions, prefix='questions')

        def post(self, *args, **kwargs):
            form_valid = self.form.is_valid()
            formset_valid = self.formset.is_valid()
            if form_valid and formset_valid:
                return self.form_valid(self.form, self.formset)
            else:
                return self.form_invalid(self.form, self.formset)

    class List(PollMixin, OrgPermsMixin, smartmin.SmartListView):
        fields = ('name', 'questions', 'pollruns', 'last_conducted')
        field_config = {'pollruns': {'label': _("Dates")}}
        link_fields = ('name', 'pollruns')
        default_order = ('name',)

        def derive_pollruns(self, obj):
            return obj.pollruns.active().by_region(
                self.request.region,
                self.request.include_subregions)

        def get_questions(self, obj):
            return obj.questions.active().count()

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
        title = _("Select Flows")
        form_class = forms.ActivePollsForm
        success_url = '@polls.poll_list'
        submit_button_name = _("Update")
        success_message = _(
            "Updated flows to track as polls." +
            " Notice: questions and categories have been scheduled to update shortly.")
        template = 'polls/poll_select.html'

        def get_form_kwargs(self):
            kwargs = super(PollCRUDL.Select, self).get_form_kwargs()
            kwargs['org'] = self.request.org
            return kwargs

        def form_valid(self, form):
            form.save()

            return super(PollCRUDL.Select, self).form_valid(form)


class PollRunListMixin(object):
    default_order = ('-conducted_on',)

    def get_conducted_on(self, obj):
        return obj.conducted_on.strftime(settings.SITE_DATE_FORMAT)

    def get_participants(self, obj):
        def calculate():
            return obj.get_response_counts(
                self.request.region, self.request.include_subregions)
        counts = get_obj_cacheable(obj, '_response_counts', calculate)
        return sum(counts.values())

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
                poll = Poll.objects.active().by_org(self.request.org).get(pk=request.POST.get('poll'))
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
            filter_form = forms.PollRunChartFilterForm(
                org=self.request.org,
                data=self.request.GET)

            if filter_form.is_valid():
                responses = self.get_responses(filter_form, self.object)
                question_data = []
                for question in self.object.poll.questions.active():
                    chart_type, chart_data, summary_table = charts.single_pollrun(
                        self.object, responses, question)
                    map_data = maps.get_map_data(responses, question)
                    question_data.append((
                        question,
                        chart_type,
                        chart_data,
                        map_data,
                        summary_table,
                    ))
            else:
                question_data = None

            kwargs.setdefault('form', filter_form)
            kwargs.setdefault('question_data', question_data)
            return super(PollRunCRUDL.Read, self).get_context_data(**kwargs)

        def get_responses(self, filter_form, pollrun):
            contacts = Contact.objects.filter(org=self.request.org)
            contacts = contacts.filter(region__is_active=True, is_active=True)
            contacts = filter_form.filter_contacts(contacts)

            if self.request.region:
                contacts = contacts.filter(region__in=self.request.data_regions)
            responses = Response.objects.active()
            responses = responses.filter(pollrun=pollrun)
            responses = responses.filter(contact__in=contacts)
            return responses

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
            return _("All Flow Runs")

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
                poll_qs = Poll.objects.active().by_org(self.request.org)
                return get_object_or_404(poll_qs, pk=self.kwargs['poll'])
            return get_obj_cacheable(self, '_poll', fetch)

        def derive_queryset(self, **kwargs):
            return self.derive_poll().pollruns.active().by_region(
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
        field_config = {
            'updated_on': {'label': _("Date")},
            'region': {'label': _('Panel')},
        }
        link_fields = ('contact',)

        def dispatch(self, request, *args, **kwargs):
            self.csv = request.GET.get('_format') == 'csv'
            return super(ResponseCRUDL.ByPollrun, self).dispatch(
                request, *args, **kwargs)

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
                for question in self.derive_pollrun().poll.questions.active():
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

        def get_paginate_by(self, queryset):
            if self.csv:
                return None
            return super(ResponseCRUDL.ByPollrun, self).get_paginate_by(queryset)

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('question_'):
                question = self.derive_questions()[field]
                return question.name
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
                    if question.question_type == Question.TYPE_RECORDING:
                        return '<a class="answer answer-audio" href="%s" data-answer-id="%d">Play</a>' % (
                            answer.value_to_use,
                            answer.pk,
                        )
                    else:
                        return answer.value_to_use
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

            if not self.csv:
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
            if self.csv:
                response = HttpResponse(content_type='text/csv', status=200)
                response['Content-Disposition'] = 'attachment; filename="responses.csv"'
                writer = unicodecsv.writer(response)

                questions = self.derive_questions().values()

                resp_headers = ['Date']
                contact_headers = ['Name', 'URN', 'Panel', 'Cohort']
                question_headers = [q.name for q in questions]
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
                        answer_cols.append(answer.value_to_use if answer else '')

                    writer.writerow(resp_cols + contact_cols + answer_cols)

                return response
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

            questions = obj.pollrun.poll.questions.active()
            for i, question in enumerate(questions, start=1):
                answer = answers_by_q_id.get(question.pk, None)
                if not answer:
                    answer_display = ""
                elif question.question_type == Question.TYPE_OPEN:
                    answer_display = answer.value_to_use
                else:
                    answer_display = answer.category

                answers.append("%d. %s: <em>%s</em>" % (
                    i, question.name, answer_display))

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
