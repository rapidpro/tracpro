from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from django import forms
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartCRUDL, SmartReadView, SmartListView, SmartFormView
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
    actions = ('read', 'list', 'select')

    class Read(OrgObjPermsMixin, SmartReadView):
        fields = ('name', 'contacts')

        def get_queryset(self):
            return self.request.user.get_regions(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(RegionCRUDL.Read, self).get_context_data(**kwargs)
            return context

        def get_contacts(self, obj):
            return obj.get_contacts().count()

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()
            return Region.get_all(org).order_by('name')

        def get_contacts(self, obj):
            return obj.get_contacts().count()

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
    actions = ('read', 'list', 'select')

    class Read(OrgObjPermsMixin, SmartReadView):
        fields = ('name', 'contacts')

        def get_queryset(self):
            return Group.get_all(self.request.org)

        def get_context_data(self, **kwargs):
            context = super(GroupCRUDL.Read, self).get_context_data(**kwargs)
            return context

        def get_contacts(self, obj):
            return obj.get_contacts().count()

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')

        def get_queryset(self, **kwargs):
            org = self.request.user.get_org()
            return Group.get_all(org).order_by('name')

        def get_contacts(self, obj):
            return obj.get_contacts().count()

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
