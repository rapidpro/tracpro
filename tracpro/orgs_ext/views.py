from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dash.orgs.views import OrgCRUDL, OrgForm, InferOrgMixin, OrgPermsMixin, SmartUpdateView
from dash.utils import ms_to_datetime
from django import forms
from django.utils.translation import ugettext_lazy as _
from smartmin.templatetags.smartmin import format_datetime
from smartmin.users.views import SmartCRUDL
from tracpro.orgs_ext import TaskType


def org_ext_context_processor(request):
    is_admin = request.org and not request.user.is_anonymous() and request.user.is_admin_for(request.org)
    return dict(user_is_admin=is_admin)


class OrgExtCRUDL(SmartCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit', 'chooser', 'choose')
    model = Org

    class Create(OrgCRUDL.Create):
        pass

    class Update(OrgCRUDL.Update):
        pass

    class List(OrgCRUDL.List):
        pass

    class Home(OrgCRUDL.Home):
        fields = ('name', 'timezone', 'facility_code_field', 'api_token', 'last_contact_sync', 'last_flow_run_fetch')
        field_config = {'api_token': {'label': _("RapidPro API Token")}}
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
        class OrgExtForm(OrgForm):
            facility_code_field = forms.ChoiceField(choices=(), label=_("Facility code field"),
                                                    help_text=_("Contact field to use as the facility code."))

            def __init__(self, *args, **kwargs):
                org = kwargs.pop('org')
                super(OrgExtCRUDL.Edit.OrgExtForm, self).__init__(*args, **kwargs)

                field_choices = []
                for field in org.get_temba_client().get_fields():
                    field_choices.append((field.key, "%s (%s)" % (field.label, field.key)))

                self.fields['facility_code_field'].choices = field_choices
                self.fields['facility_code_field'].initial = org.get_facility_code_field()

            class Meta:
                model = Org

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
            from . import ORG_CONFIG_FACILITY_CODE_FIELD
            obj = super(OrgExtCRUDL.Edit, self).pre_save(obj)
            obj.set_config(ORG_CONFIG_FACILITY_CODE_FIELD, self.form.cleaned_data['facility_code_field'])
            return obj

    class Chooser(OrgCRUDL.Chooser):
        pass

    class Choose(OrgCRUDL.Choose):
        pass
