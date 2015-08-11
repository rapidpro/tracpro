from django.core.urlresolvers import reverse

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView, SmartDeleteView, SmartListView
    )

from .models import BaselineTerm
from .forms import BaselineTermForm


class BaselineTermCRUDL(SmartCRUDL):
    model = BaselineTerm
    actions = ('create', 'read', 'update', 'delete', 'list')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = BaselineTermForm

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'start_date', 'end_date', 'baseline_question', 'follow_up_question')
        link_fields = ('name')

        def derive_queryset(self, **kwargs):
            qs = BaselineTerm.get_all(self.request.org)
            qs = qs.order_by('-start_date', '-end_date')
            return qs

    class Delete(OrgObjPermsMixin, SmartDeleteView):
        def get_redirect_url(self):
            return reverse('baseline.baselineterm_list')
