from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView, SmartDeleteView,
    SmartListView, SmartReadView, SmartUpdateView
)

from .models import BaselineTerm
from .forms import BaselineTermForm


class BaselineTermCRUDL(SmartCRUDL):
    model = BaselineTerm
    actions = ('create', 'read', 'update', 'delete', 'list')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = BaselineTermForm

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
