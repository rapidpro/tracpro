from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgCRUDL, InferOrgMixin, OrgPermsMixin
from dash.utils import ms_to_datetime

from django.utils.translation import ugettext_lazy as _

from smartmin.templatetags.smartmin import format_datetime
from smartmin.views import SmartUpdateView

from . import ORG_CONFIG_FACILITY_CODE_FIELD, TaskType
from .forms import OrgExtForm


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

        def derive_title(self):
            return _("My Organization")

        def get_facility_code_field(self, obj):
            return obj.get_facility_code_field()

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
        fields = ('name', 'timezone', 'facility_code_field')
        permission = 'orgs.org_edit'
        title = _("Edit My Organization")
        success_url = '@orgs_ext.org_home'
        form_class = OrgExtForm

        def get_form_kwargs(self):
            kwargs = super(OrgExtCRUDL.Edit, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def pre_save(self, obj):
            obj = super(OrgExtCRUDL.Edit, self).pre_save(obj)
            obj.set_config(ORG_CONFIG_FACILITY_CODE_FIELD,
                           self.form.cleaned_data['facility_code_field'])
            return obj
