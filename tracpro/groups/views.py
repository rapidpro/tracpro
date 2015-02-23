from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartListView, SmartFormView
from .models import Group, Region


class ContactGroupsForm(forms.Form):
    groups = forms.MultipleChoiceField(choices=(), label=_("Groups"),
                                       help_text=_("Contact groups to use."))

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org')
        initial = kwargs.pop('initial')

        super(ContactGroupsForm, self).__init__(*args, **kwargs)

        choices = []
        for group in org.get_temba_client().get_groups():
            choices.append((group.uuid, "%s (%d)" % (group.name, group.size)))

        self.fields['groups'].choices = choices
        self.fields['groups'].initial = initial


class RegionCRUDL(SmartCRUDL):
    model = Region
    actions = ('list', 'most_active', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')
        default_order = ('name',)

        def derive_queryset(self, **kwargs):
            return Region.get_all(self.request.org)

        def get_contacts(self, obj):
            return obj.get_contacts().count()

    class MostActive(OrgPermsMixin, SmartListView):
        def get(self, request, *args, **kwargs):
            regions = Region.get_most_active(self.request.org)[0:5]
            results = [{'id': r.pk, 'name': r.name, 'response_count': r.response_count} for r in regions]
            return JsonResponse({'count': len(results), 'results': results})

    class Select(OrgPermsMixin, SmartFormView):
        title = _("Region Groups")
        form_class = ContactGroupsForm
        success_url = '@groups.region_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as regions")

        def get_form_kwargs(self):
            kwargs = super(RegionCRUDL.Select, self).get_form_kwargs()
            org = self.request.org
            kwargs['org'] = org
            kwargs['initial'] = [r.uuid for r in Region.get_all(org)]
            return kwargs

        def form_valid(self, form):
            Region.sync_with_groups(self.request.user.get_org(), form.cleaned_data['groups'])
            return HttpResponseRedirect(self.get_success_url())


class GroupCRUDL(SmartCRUDL):
    model = Group
    actions = ('list', 'most_active', 'select')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')
        default_order = ('name',)
        title = _("Reporter Groups")

        def derive_queryset(self, **kwargs):
            return Group.get_all(self.request.org)

        def get_contacts(self, obj):
            return obj.get_contacts().count()

    class MostActive(OrgPermsMixin, SmartListView):
        def get(self, request, *args, **kwargs):
            regions = Group.get_most_active(self.request.org)[0:5]
            results = [{'id': r.pk, 'name': r.name, 'response_count': r.response_count} for r in regions]
            return JsonResponse({'count': len(results), 'results': results})

    class Select(OrgPermsMixin, SmartFormView):
        title = _("Reporter Groups")
        form_class = ContactGroupsForm
        success_url = '@groups.group_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as reporter groups")

        def get_form_kwargs(self):
            kwargs = super(GroupCRUDL.Select, self).get_form_kwargs()
            org = self.request.org
            kwargs['org'] = org
            kwargs['initial'] = [r.uuid for r in Group.get_all(org)]
            return kwargs

        def form_valid(self, form):
            Group.sync_with_groups(self.request.user.get_org(), form.cleaned_data['groups'])
            return HttpResponseRedirect(self.get_success_url())
