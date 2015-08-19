from django.core.urlresolvers import reverse

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
        fields = ('name', 'region', 'start_date', 'end_date',
                  'baseline_question', 'follow_up_question')
        link_fields = ('name')

        def derive_queryset(self, **kwargs):
            regions = [self.request.region] if self.request.region else None
            qs = BaselineTerm.get_all(self.request.org, regions)
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
            regions = self.request.user.get_regions(self.request.org)
            return BaselineTerm.get_all(self.request.org, regions)

        def get_form_kwargs(self):
            kwargs = super(BaselineTermCRUDL.Update, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

    class Read(OrgObjPermsMixin, SmartReadView):

        def derive_queryset(self, **kwargs):
            regions = self.request.user.get_regions(self.request.org)
            return BaselineTerm.get_all(self.request.org, regions)

        def get_context_data(self, **kwargs):
            context = super(BaselineTermCRUDL.Read, self).get_context_data(**kwargs)

            baselines = self.object.get_baseline(region=self.object.region)
            follow_ups, dates = self.object.get_follow_up(region=self.object.region)

            baseline_dict = {}
            for baseline in baselines:
                baseline_dict[baseline[2]] = {}
                baseline_dict[baseline[2]]["value"] = float(baseline[1])
            context['baseline_dict'] = baseline_dict

            date_list = []
            for date in dates:
                date_formatted = date[0].strftime('%m/%d')
                date_list.append(date_formatted)
            context['date_list'] = date_list
            context['date_count'] = range(len(date_list))

            answers_dict = {}
            for follow_up in follow_ups:
                answers_dict[follow_up] = {}
                answers_dict[follow_up]["dates"] = [date.strftime("%m/%d") for date in follow_ups[follow_up]["dates"]]
                """
                TODO: I might want to check to see if the date exists
                for this value before inserting it into the list
                """
                answers_dict[follow_up]["values"] = [float(val) for val in follow_ups[follow_up]["values"]]
            context['answers_dict'] = answers_dict

            return context
