from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
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


class MakeAdminsIntoStaffMixin(object):
    # Make sure all admins are staff users.
    def post_save(self, obj):
        obj.get_org_admins().filter(is_staff=False).update(is_staff=True)
        return super(MakeAdminsIntoStaffMixin, self).post_save(obj)


class OrgExtCRUDL(OrgCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit', 'chooser',
               'choose', 'fetchruns')

    class Chooser(OrgCRUDL.Chooser):
        def dispatch(self, request, *args, **kwargs):
            if request.org:
                # We have an org, no need for the chooser view
                return redirect(reverse('home.home'))
            return super(OrgExtCRUDL.Chooser, self).dispatch(request, *args, **kwargs)

    class Create(MakeAdminsIntoStaffMixin, OrgCRUDL.Create):
        form_class = forms.OrgExtForm
        fields = ('name', 'available_languages', 'language',
                  'timezone', 'subdomain', 'api_token', 'google_analytics', 'show_spoof_data',
                  'logo', 'administrators')

    class List(OrgCRUDL.List):
        default_order = ('name',)

    class Update(MakeAdminsIntoStaffMixin, OrgCRUDL.Update):
        form_class = forms.OrgExtForm
        fields = ('is_active', 'name', 'available_languages', 'language',
                  'contact_fields', 'timezone', 'subdomain', 'api_token', 'google_analytics',
                  'show_spoof_data', 'logo', 'administrators',
                  'how_to_handle_sameday_responses',
                  )

    class Home(OrgCRUDL.Home):
        fields = ('name', 'timezone', 'api_token', 'google_analytics', 'last_contact_sync',
                  'last_flow_run_fetch')
        field_config = {
            'api_token': {
                'label': _("RapidPro API Token"),
            },
        }
        permission = 'orgs.org_home'
        title = _("My Organization")

        def get_google_analytics(self, obj):
            return obj.get_config("google_analytics", "")

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
        fields = ('name', 'timezone', 'contact_fields', 'logo', 'google_analytics')
        form_class = forms.OrgExtForm
        permission = 'orgs.org_edit'
        success_url = '@orgs_ext.org_home'
        title = _("Edit My Organization")

    class Fetchruns(InferOrgMixin, OrgPermsMixin, SmartFormView):
        form_class = forms.FetchRunsForm
        permission = 'orgs.org_fetch_runs'
        success_url = '@orgs_ext.org_home'
        title = _("Fetch past runs for my organization")
        template_name = 'polls/fetch_runs.html'

        def form_valid(self, form):
            org = self.get_object()
            howfarback = relativedelta(days=form.cleaned_data['days'])
            since = timezone.now() - howfarback
            email = self.request.user.email
            tasks.fetch_runs.delay(org.id, since, email)
            success_message = _("We have scheduled a fetch in the background. An email will be "
                                "sent to {email} when the fetch has completed.").format(email=email)
            messages.success(self.request, success_message)
            return super(SmartFormView, self).form_valid(form)
