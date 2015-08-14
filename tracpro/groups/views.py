from __future__ import absolute_import, unicode_literals

import json

from dash.orgs.views import OrgPermsMixin

from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from smartmin.users.views import (
    SmartCRUDL, SmartListView, SmartFormView, SmartView)

from tracpro.contacts.models import Contact

from .models import Group, Region
from .forms import ContactGroupsForm


class RegionCRUDL(SmartCRUDL):
    model = Region
    actions = ('list', 'most_active', 'select', 'update_hierarchy')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'contacts')
        paginate_by = None

        def derive_queryset(self, **kwargs):
            regions = Region.get_all(self.request.org)
            regions = regions.prefetch_related(
                Prefetch(
                    "contacts",
                    Contact.objects.filter(is_active=True),
                    "prefetched_contacts",
                ),
            )
            return regions

        def get_contacts(self, obj):
            return len(obj.prefetched_contacts)

    class MostActive(OrgPermsMixin, SmartListView):

        def get(self, request, *args, **kwargs):
            regions = Region.get_most_active(self.request.org)[0:5]
            results = [{'id': r.pk, 'name': r.name, 'response_count': r.response_count}
                       for r in regions]
            return JsonResponse({
                'count': len(results),
                'results': results,
            })

    class Select(OrgPermsMixin, SmartFormView):
        title = _("Region Groups")
        form_class = ContactGroupsForm
        success_url = '@groups.region_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as regions")

        def get_form_kwargs(self):
            kwargs = super(RegionCRUDL.Select, self).get_form_kwargs()
            kwargs.setdefault('model', RegionCRUDL.model)
            kwargs.setdefault('org', self.request.org)
            return kwargs

        def form_valid(self, form):
            form.sync_contacts()
            return HttpResponseRedirect(self.get_success_url())

    class UpdateHierarchy(OrgPermsMixin, SmartView, View):
        http_method_names = ['post']

        @transaction.atomic
        def post(self, request, *args, **kwargs):
            """AJAX endpoint to update Region hierarchy at once."""
            try:
                data = json.loads(request.POST.get('data'))
            except (TypeError, ValueError):
                return self.error_response(400, "Bad JSON.")
            else:
                if not isinstance(data, dict):
                    return self.error_response(400, "Invalid format.")

            # Grab all org regions.
            regions = {str(r.pk): r for r in Region.get_all(request.org)}

            # Check that the user is updating exactly the regions for this org.
            sent_ids = set(str(i) for i in data.keys() + data.values() if i is not None)
            if sent_ids != set(regions.keys()):
                return self.error_response(400, "ID mismatch.")

            with Region.objects.delay_mptt_updates():
                for region_id, parent_id in data.items():
                    region = regions.get(str(region_id))
                    parent = regions.get(str(parent_id))
                    if region.parent != parent:
                        region.parent = parent
                        region.save()

            message = '{org.name} region hierarchy has been updated.'
            message = message.format(org=request.org)
            return self.success_response(message)

        def error_response(self, status, message):
            return JsonResponse({
                'status': status,
                'success': False,
                'message': message,
            })

        def success_response(self, message):
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': message,
            })


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
            results = [{'id': r.pk, 'name': r.name, 'response_count': r.response_count}
                       for r in regions]
            return JsonResponse({
                'count': len(results),
                'results': results,
            })

    class Select(OrgPermsMixin, SmartFormView):
        title = _("Reporter Groups")
        form_class = ContactGroupsForm
        success_url = '@groups.group_list'
        submit_button_name = _("Update")
        success_message = _("Updated contact groups to use as reporter groups")

        def get_form_kwargs(self):
            kwargs = super(GroupCRUDL.Select, self).get_form_kwargs()
            kwargs.setdefault('model', GroupCRUDL.model)
            kwargs.setdefault('org', self.request.org)
            return kwargs

        def form_valid(self, form):
            form.sync_contacts()
            return HttpResponseRedirect(self.get_success_url())
