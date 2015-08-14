from django.core.urlresolvers import reverse

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView, SmartDeleteView,
    SmartListView, SmartReadView, SmartUpdateView
)

from tracpro.polls.models import Answer
from .models import BaselineTerm
from .forms import BaselineTermForm
from .charts import baseline_chart


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

            context['baseline_answers'] = self.object.get_baseline(region=self.object.region)
            context['follow_up_answers'] = self.object.get_follow_up(region=self.object.region)

            baseline_chart(context['baseline_answers'])

            return context
