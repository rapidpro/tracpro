from datetime import datetime
from dateutil import rrule
import pytz
import random

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.views.generic import View

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView, SmartDeleteView,
    SmartListView, SmartReadView, SmartUpdateView,
    SmartView
)
from smartmin.users.views import SmartFormView

from tracpro.polls.models import Answer, PollRun, Response

from .models import BaselineTerm
from .forms import BaselineTermForm, SpoofDataForm
from .utils import chart_baseline


class BaselineTermCRUDL(SmartCRUDL):
    model = BaselineTerm
    actions = ('create', 'read', 'update', 'delete', 'list', 'data_spoof', 'clear_spoof')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = BaselineTermForm
        success_url = 'id@baseline.baselineterm_read'

        def get_form_kwargs(self):
            kwargs = super(BaselineTermCRUDL.Create, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'start_date', 'end_date',
                  'baseline_question', 'follow_up_question')
        link_fields = ('name')

        def derive_queryset(self, **kwargs):
            qs = BaselineTerm.get_all(self.request.org)
            qs = qs.order_by('-start_date', '-end_date')
            return qs

    class Delete(OrgObjPermsMixin, SmartDeleteView):
        cancel_url = '@baseline.baselineterm_list'

        def get_redirect_url(self):
            return reverse('baseline.baselineterm_list')

    class Update(OrgObjPermsMixin,  SmartUpdateView):
        form_class = BaselineTermForm
        delete_url = ''     # Turn off the smartmin delete button for this view
        success_url = 'id@baseline.baselineterm_read'

        def derive_queryset(self, **kwargs):
            return BaselineTerm.get_all(self.request.org)

        def get_form_kwargs(self):
            kwargs = super(BaselineTermCRUDL.Update, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

    class Read(OrgObjPermsMixin, SmartReadView):
        fields = ("start_date", "end_date", "baseline_poll", "baseline_question",
                  "follow_up_poll", "follow_up_question")

        def derive_queryset(self, **kwargs):
            return BaselineTerm.get_all(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(BaselineTermCRUDL.Read, self).get_context_data(**kwargs)

            # Get the region from the region filter drop-down, if it was selected
            try:
                region = int(self.request.GET.get('region', 0))
            except ValueError:
                region = None
                context['error_message'] = _(
                    "%s is not a valid region. Please select a valid region from the drop-down."
                    % (self.request.GET.get('region', '')))

            if region:
                region_selected = region
                context['region_selected'] = region_selected
            else:
                region_selected = None

            (follow_up_list, baseline_list, all_regions, date_list,
             baseline_mean, baseline_std, follow_up_mean, follow_up_std) = chart_baseline(
                self.object, self.request.data_regions, region_selected)

            context['all_regions'] = all_regions
            context['date_list'] = date_list
            context['baseline_list'] = baseline_list
            context['follow_up_list'] = follow_up_list
            context['baseline_mean'] = baseline_mean
            context['baseline_std'] = baseline_std
            context['follow_up_mean'] = follow_up_mean
            context['follow_up_std'] = follow_up_std
            context['include_legend_data'] = 1

            if len(context['follow_up_list']) == 0 and len(context['baseline_list']) == 0:
                context['error_message'] = _(
                    "No data exists for this baseline chart. You may need to select a different region.")

            return context

    class DataSpoof(OrgPermsMixin, SmartFormView):
        title = _("Baseline Term Data Spoof")
        template_name = 'baseline/baselineterm_data.html'
        form_class = SpoofDataForm
        cancel_url = '@baseline.baselineterm_list'
        success_url = '@baseline.baselineterm_list'

        def get_form_kwargs(self):
            kwargs = super(BaselineTermCRUDL.DataSpoof, self).get_form_kwargs()
            kwargs.setdefault('org', self.request.org)
            return kwargs

        def random_answer_calculate(self, min_value, max_value):
            random_value = min_value if min_value == max_value else random.randrange(min_value, max_value)
            return random_value

        def create_baseline(self, poll, date, contacts, baseline_question, baseline_minimum, baseline_maximum):
            baseline_datetime = datetime.combine(date, datetime.utcnow().time().replace(tzinfo=pytz.utc))
            baseline_pollrun = PollRun.objects.create_spoofed(
                poll=poll, conducted_on=baseline_datetime)
            for contact in contacts:
                # Create a Response AKA FlowRun for each contact for Baseline
                response = Response.objects.create(
                    pollrun=baseline_pollrun,
                    contact=contact,
                    created_on=baseline_datetime,
                    updated_on=baseline_datetime,
                    status=Response.STATUS_COMPLETE,
                    is_active=True)
                random_answer = self.random_answer_calculate(baseline_minimum, baseline_maximum)
                # Create a randomized Answer for each contact for Baseline
                Answer.objects.create(
                    response=response,
                    question=baseline_question,
                    value=random_answer,
                    submitted_on=baseline_datetime,
                    category=u'')

        def form_valid(self, form):
            baseline_question = self.form.cleaned_data['baseline_question']
            follow_up_question = self.form.cleaned_data['follow_up_question']
            contacts = self.form.cleaned_data['contacts']
            baseline_minimum = self.form.cleaned_data['baseline_minimum']
            baseline_maximum = self.form.cleaned_data['baseline_maximum']
            follow_up_minimum = self.form.cleaned_data['follow_up_minimum']
            follow_up_maximum = self.form.cleaned_data['follow_up_maximum']
            start = self.form.cleaned_data['start_date']
            end = self.form.cleaned_data['end_date']

            # Create a single PollRun for the Baseline Poll for all contacts
            self.create_baseline(baseline_question.poll, start, contacts,
                                 baseline_question, baseline_minimum, baseline_maximum)

            # Create a PollRun for each date from start to end dates for the Follow Up Poll
            for loop_count, follow_up_date in enumerate(rrule.rrule(rrule.DAILY, dtstart=start, until=end)):
                follow_up_datetime = datetime.combine(follow_up_date, datetime.utcnow().time().replace(tzinfo=pytz.utc))
                follow_up_pollrun = PollRun.objects.create_spoofed(
                    poll=follow_up_question.poll, conducted_on=follow_up_datetime)
                for contact in contacts:
                    # Create a Response AKA FlowRun for each contact for Follow Up
                    response = Response.objects.create(
                        pollrun=follow_up_pollrun,
                        contact=contact,
                        created_on=follow_up_datetime,
                        updated_on=follow_up_datetime,
                        status=Response.STATUS_COMPLETE,
                        is_active=True)
                    random_answer = self.random_answer_calculate(follow_up_minimum, follow_up_maximum)
                    # Create a randomized Answer for each contact for Follow Up
                    Answer.objects.create(
                        response=response,
                        question=follow_up_question,
                        value=random_answer,
                        submitted_on=follow_up_datetime,
                        category=u'')
                loop_count += 1

            return HttpResponseRedirect(self.get_success_url())

    class ClearSpoof(OrgPermsMixin, SmartView, View):

        def post(self, request, *args, **kwargs):
            # Spoofed data has TYPE_SPOOFED. Filter only for current org.
            pollruns = PollRun.objects.filter(pollrun_type=PollRun.TYPE_SPOOFED,
                                              poll__org=self.request.org)

            # This will create a cascading delete to clear out all Spoofed Poll data
            # from PollRun, Answer and Response
            pollruns.delete()

            return HttpResponseRedirect(reverse('baseline.baselineterm_list'))
