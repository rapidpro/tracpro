from __future__ import absolute_import, unicode_literals

import logging
import json

from dash.orgs.views import OrgPermsMixin

from django.db import transaction
from django.db.models import Prefetch
from django.http import (
    HttpResponseBadRequest, HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from smartmin.users.views import (
    SmartCRUDL, SmartListView, SmartFormView, SmartView)

from tracpro.contacts.models import Contact

from .models import Group, Region
from .forms import ContactGroupsForm


logger = logging.getLogger(__name__)


class ToggleSubregions(View):
    post_param = "include_subregions"
    next_param = "next"
    session_param = "include_subregions"

    def post(self, request, *args, **kwargs):
        """
        Update session variable that manages whether to include data for
        sub-regions, or only the current region.
        """
        if self.post_param not in request.POST or self.next_param not in request.POST:
            raise HttpResponseBadRequest(
                "Request should include '{}' and '{}'.".format(
                    self.post_param, self.next_param))

        val = request.POST.get(self.post_param)
        if val in ('0', '1'):
            request.session[self.session_param] = bool(int(val))
            request.session.save()
        else:
            raise HttpResponseBadRequest(
                "{} should be either '0' or '1'".format(
                    self.post_param))

        # Redirect to the next path.
        # TODO: Double-check validation of `next` parameter.
        next_path = request.POST.get(self.next_param)
        return redirect(next_path)


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
            uuids = form.cleaned_data['groups']
            Region.sync_with_temba(self.request.org, uuids)
            return HttpResponseRedirect(self.get_success_url())

    class UpdateHierarchy(OrgPermsMixin, SmartView, View):
        http_method_names = ['post']

        @transaction.atomic
        def post(self, request, *args, **kwargs):
            """AJAX endpoint to update Region hierarchy at once."""
            org = request.org

            # Load data and validate that it is in the correct format.
            raw_data = request.POST.get('data', "").strip() or None
            try:
                data = json.loads(raw_data)
            except TypeError:
                msg = "No data was provided in the `data` parameter."
                logger.warning("{} Hierarchy: {}".format(org, msg), exc_info=True)
                return self.error_response(400, msg)
            except ValueError:
                msg = "Data must be valid JSON."
                logger.warning("{} Hierarchy: {} {}".format(org, msg, raw_data), exc_info=True)
                return self.error_response(400, msg)
            if not isinstance(data, dict):
                msg = "Data must be a dict that maps region id to parent id."
                logger.warning("{} Hierarchy: {} {}".format(org, msg, raw_data))
                return self.error_response(400, msg)

            # Grab all of the org's regions at once.
            regions = {str(r.pk): r for r in Region.get_all(org)}

            # Check that the user is updating exactly the regions from this
            # org, and that specified parents are regions from this org.
            expected_ids = set(regions.keys())
            sent_regions = set(str(i) for i in data.keys())
            sent_parents = set(str(i) for i in data.values() if i is not None)
            if sent_regions != expected_ids:
                msg = ("Data must map region id to parent id for each "
                       "region in this org.")
                logger.warning("{} Hierarchy: {} {}".format(org, msg, raw_data))
                return self.error_response(400, msg)
            elif not sent_parents.issubset(expected_ids):
                msg = ("Region parent must be a region from the same org, "
                       "or null.")
                logger.warning("{} Hierarchy: {} {}".format(org, msg, raw_data))
                return self.error_response(400, msg)

            # Re-set parent values for each region, then rebuild the mptt tree.
            with Region.objects.disable_mptt_updates():
                for region_id, parent_id in data.items():
                    region = regions.get(str(region_id))
                    parent = regions.get(str(parent_id))
                    if region.parent != parent:
                        old = region.parent.name if region.parent else None
                        new = parent.name if parent else None
                        msg = "Updating parent of {} from {} -> {}".format(region, old, new)
                        logger.debug("{} Hierarchy: {}".format(org, msg))
                        region.parent = parent
                        region.save()
            Region.objects.rebuild()

            msg = '{} region hierarchy has been updated.'.format(org.name)
            logger.info("{} Hierarchy: {} {}".format(org, msg, raw_data))
            return self.success_response(msg)

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
            uuids = form.cleaned_data['groups']
            Group.sync_with_temba(self.request.org, uuids)
            return HttpResponseRedirect(self.get_success_url())
