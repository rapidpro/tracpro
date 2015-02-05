from __future__ import absolute_import, unicode_literals

from dash.orgs.models import Org
from dash.orgs.views import OrgCRUDL, InferOrgMixin, OrgPermsMixin, SmartUpdateView
from django import forms
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL


def org_ext_context_processor(request):
    is_admin = request.org and not request.user.is_anonymous() and request.user.is_admin_for(request.org)
    return dict(user_is_admin=is_admin)


class OrgExtCRUDL(SmartCRUDL):
    actions = ('create', 'update', 'list', 'home', 'edit')
    model = Org

    class Create(OrgCRUDL.Create):
        pass

    class Update(OrgCRUDL.Update):
        pass

    class List(OrgCRUDL.List):
        pass

    class Home(OrgCRUDL.Home):
        fields = ('name', 'api_token')
        field_config = {'api_token': {'label': _("RapidPro API Token")}}
        permission = 'orgs.org_home'

        def derive_title(self):
            return _("My Organization")

    class Edit(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        class OrgForm(forms.ModelForm):
            secret_token = forms.CharField(label=_("Secret token"),
                                           help_text=_("Secret token for all calls from RapidPro."))

            def __init__(self, *args, **kwargs):
                org = kwargs.pop('org')
                super(OrgExtCRUDL.Edit.OrgForm, self).__init__(*args, **kwargs)

                field_choices = []
                for field in org.get_temba_client().get_fields():
                    field_choices.append((field.key, "%s (%s)" % (field.label, field.key)))

                self.fields['secret_token'].initial = org.get_secret_token()

            class Meta:
                model = Org

        fields = ('name', 'secret_token')
        form_class = OrgForm
        permission = 'orgs.org_edit'
        title = _("Edit My Organization")
        success_url = '@orgs_ext.org_home'

        def get_form_kwargs(self):
            kwargs = super(OrgExtCRUDL.Edit, self).get_form_kwargs()
            kwargs['org'] = self.request.user.get_org()
            return kwargs

        def pre_save(self, obj):
            from . import ORG_CONFIG_SECRET_TOKEN
            obj = super(OrgExtCRUDL.Edit, self).pre_save(obj)
            obj.set_config(ORG_CONFIG_SECRET_TOKEN, self.form.cleaned_data['secret_token'])
            return obj
