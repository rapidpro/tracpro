from django.shortcuts import redirect

from dash.orgs.views import OrgPermsMixin

from smartmin.views import (
    SmartCRUDL, SmartCreateView
    )

from .models import BaselineTerm
from .forms import BaselineTermForm


class BaselineTermCRUDL(SmartCRUDL):
    model = BaselineTerm
    actions = ('create', 'list')

    class Create(OrgPermsMixin, SmartCreateView):
        form_class = BaselineTermForm

        def post(self, request, *args, **kwargs):
            form = BaselineTermForm(data=request.POST)

            if form.is_valid():
                post = super(BaselineTermCRUDL.Create, self).post(self, request)
                return redirect('baseline.baselineterm_list')
            else:
                return self.get(request, *args, **kwargs)
