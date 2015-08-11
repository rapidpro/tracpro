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
