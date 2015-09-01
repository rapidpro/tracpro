from datetime import datetime
from dateutil import rrule
import random

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView, SmartDeleteView,
    SmartListView, SmartReadView, SmartUpdateView
)
from smartmin.users.views import SmartFormView

from .models import BaselineTerm
from .forms import BaselineTermForm, SpoofDataForm
from tracpro.polls.models import (
    Answer, PollRun, Response, RESPONSE_COMPLETE
)


class BaselineTermCRUDL(SmartCRUDL):
    model = BaselineTerm
    actions = ('create', 'read', 'update', 'delete', 'list', 'data_spoof')

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

        def derive_queryset(self, **kwargs):
            return BaselineTerm.get_all(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(BaselineTermCRUDL.Read, self).get_context_data(**kwargs)

            region = self.request.region

            baseline_dict = self.object.get_baseline(region=region)
            context['baseline_dict'] = baseline_dict

            follow_ups, dates = self.object.get_follow_up(region=region)

            date_list = []
            for date in dates:
                date_formatted = date.strftime('%m/%d')
                date_list.append(date_formatted)
            context['date_list'] = date_list
            context['date_count'] = range(len(date_list))

            answers_dict = {}
            for follow_up in follow_ups:
                answers_dict[follow_up] = {}
                answers_dict[follow_up]["values"] = [float(val) for val in follow_ups[follow_up]["values"]]
            context['answers_dict'] = answers_dict

            if len(context['answers_dict']) == 0 and len(context['baseline_dict']) == 0:
                context['error_message'] = _(
                    "No data exists for this baseline chart. You may need to select a different region.")

            return context

    class DataSpoof(OrgPermsMixin, SmartFormView):
        title = _("Baseline Term Data Spoof")
        template_name = 'baseline/baselineterm_data.html'
        form_class = SpoofDataForm
        success_url = '@baseline.baselineterm_list'

        def get_form_kwargs(self):
            kwargs = super(BaselineTermCRUDL.DataSpoof, self).get_form_kwargs()
            kwargs.setdefault('org', self.request.org)
            return kwargs

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

            # Create a single PollRun for the Baseline Poll
            baseline_datetime = datetime.combine(start, datetime.now().time())
            baseline_pollrun = PollRun.objects.create(poll=baseline_question.poll, conducted_on=baseline_datetime)
            for contact in contacts:
                # Create a Response AKA FlowRun for each contact for Baseline
                response = Response.objects.create(
                    pollrun=baseline_pollrun,
                    contact=contact,
                    created_on=baseline_datetime,
                    updated_on=baseline_datetime,
                    status=RESPONSE_COMPLETE,
                    is_active=True)
                random_answer = random.randrange(baseline_minimum, baseline_maximum)
                # Create a randomized Answer for each contact for Baseline
                Answer.objects.create(
                    response=response,
                    question=baseline_question,
                    value=random_answer,
                    submitted_on=baseline_datetime,
                    category=u'')

            # Create a PollRun for each date from start to end dates for the Follow Up Poll
            for follow_up_date in rrule.rrule(rrule.DAILY, dtstart=start, until=end):
                follow_up_datetime = datetime.combine(follow_up_date, datetime.now().time())
                follow_up_pollrun = PollRun.objects.create(
                    poll=follow_up_question.poll, conducted_on=follow_up_datetime)
                for contact in contacts:
                    # Create a Response AKA FlowRun for each contact for Follow Up
                    response = Response.objects.create(
                        pollrun=follow_up_pollrun,
                        contact=contact,
                        created_on=follow_up_datetime,
                        updated_on=follow_up_datetime,
                        status=RESPONSE_COMPLETE,
                        is_active=True)
                    random_answer = random.randrange(follow_up_minimum, follow_up_maximum)
                    # Create a randomized Answer for each contact for Follow Up
                    Answer.objects.create(
                        response=response,
                        question=follow_up_question,
                        value=random_answer,
                        submitted_on=follow_up_datetime,
                        category=u'')

            return HttpResponseRedirect(self.get_success_url())
