from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dash.orgs.views import OrgCRUDL, InferOrgMixin, OrgPermsMixin
from dash.utils import ms_to_datetime
from dateutil.relativedelta import relativedelta

from smartmin.templatetags.smartmin import format_datetime
from smartmin.views import SmartUpdateView, SmartFormView

from . import constants
from . import forms
from . import tasks


class OrgExtCRUDL(OrgCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit', 'chooser',
               'choose', 'fetchruns')

    class Create(OrgCRUDL.Create):
        form_class = forms.OrgExtForm
        fields = ('name', 'available_languages', 'language',
                  'timezone', 'subdomain', 'api_token', 'show_spoof_data',
                  'logo', 'administrators')

    class List(OrgCRUDL.List):
        default_order = ('name',)

    class Update(OrgCRUDL.Update):
        form_class = forms.OrgExtForm
        fields = ('is_active', 'name', 'available_languages', 'language',
                  'contact_fields', 'timezone', 'subdomain', 'api_token',
                  'show_spoof_data', 'logo', 'administrators')

    class Home(OrgCRUDL.Home):
        fields = ('name', 'timezone', 'api_token', 'last_contact_sync',
                  'last_flow_run_fetch')
        field_config = {
            'api_token': {
                'label': _("RapidPro API Token"),
            },
        }
        permission = 'orgs.org_home'
        title = _("My Organization")

        def get_last_contact_sync(self, obj):
            result = obj.get_task_result(constants.TaskType.sync_contacts)
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
            result = obj.get_task_result(constants.TaskType.fetch_runs)
            if result:
                return "%s (%d fetched)" % (
                    format_datetime(ms_to_datetime(result['time'])),
                    result.get('counts', {}).get('fetched', 0)
                )
            else:
                return None

    class Edit(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        fields = ('name', 'timezone', 'contact_fields', 'logo')
        form_class = forms.OrgExtForm
        permission = 'orgs.org_edit'
        success_url = '@orgs_ext.org_home'
        title = _("Edit My Organization")

    class Fetchruns(InferOrgMixin, SmartFormView):
        form_class = forms.FetchRunsForm
        permission = 'orgs.org_edit'
        success_message = _("Scheduled a fetch in the background")
        title = _("Fetch past runs for my organization")

        def form_valid(self, form):
            org = self.get_object()
            howfarback = relativedelta(
                minutes=form.cleaned_data.get('minutes') or 0,
                hours=form.cleaned_data.get('hours') or 0,
                days=form.cleaned_data.get('days') or 0)
            since = timezone.now() - howfarback
            tasks.fetch_runs.delay(org.id, since)
            messages.success(self.request, self.derive_success_message())
            return super(SmartFormView, self).form_valid(form)
