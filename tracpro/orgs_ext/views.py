from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgCRUDL, InferOrgMixin, OrgPermsMixin
from dash.utils import ms_to_datetime

from django.utils.translation import ugettext_lazy as _

from smartmin.templatetags.smartmin import format_datetime
from smartmin.views import SmartUpdateView

from .constants import TaskType
from .forms import SimpleOrgEditForm


class OrgExtCRUDL(OrgCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit', 'chooser',
               'choose')

    class Home(OrgCRUDL.Home):
        fields = ('name', 'timezone', 'facility_code_field', 'api_token',
                  'last_contact_sync', 'last_flow_run_fetch')
        field_config = {
            'api_token': {
                'label': _("RapidPro API Token"),
            },
        }
        permission = 'orgs.org_home'
        title = _("My Organization")

        def get_last_contact_sync(self, obj):
            result = obj.get_task_result(TaskType.sync_contacts)
            if result:
                return "%s (%d created, %d updated, %d deleted, %d failed)" % (
                    format_datetime(ms_to_datetime(result['time'])),
                    result['counts']['created'],
                    result['counts']['updated'],
                    result['counts']['deleted'],
                    result['counts']['failed'],
                )
            else:
                return None

        def get_last_flow_run_fetch(self, obj):
            result = obj.get_task_result(TaskType.fetch_runs)
            if result:
                return format_datetime(ms_to_datetime(result['time']))
            else:
                return None

    class Edit(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        form_class = SimpleOrgEditForm
        permission = 'orgs.org_edit'
        success_url = '@orgs_ext.org_home'
        title = _("Edit My Organization")
