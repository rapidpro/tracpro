from __future__ import absolute_import, unicode_literals

import logging
import json

from dash.orgs.views import OrgPermsMixin

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Prefetch
from django.http import (
    HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, HttpResponse)
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.list import ListView

from smartmin.users.views import (
    SmartCRUDL, SmartListView, SmartFormView, SmartView)

from tracpro.contacts.models import Contact

from .models import Boundary, Group, Region
from .forms import ContactGroupsForm


logger = logging.getLogger(__name__)


class SetRegion(View):
    """
    Update the session variable that stores the currently-active region
    per org.
    """

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if 'region' not in request.POST:
            return HttpResponseBadRequest(
                "Request data should include `region`.")

        # Determine the requested region.
        region_id = request.POST.get('region')
        if region_id == "all":
            if not request.user.is_admin_for(request.org):
                return HttpResponseBadRequest(
                    "Only org admins may see all regions.")
            else:
                region = None
        else:
            region = request.user_regions.filter(pk=region_id).first()
            if not region:
                return HttpResponseBadRequest(
                    "Either region {} does not exist or you do not have "
                    "permission to see this region.".format(region_id))

        # Show a message confirming the change.
        region_name = region.name if region else "all regions"
        msg = "Now showing data from {}.".format(region_name)
        messages.info(request, msg)

        # Store the requested region in the session.
        session_key = '{org}:region_id'.format(org=request.org.pk)
        request.session[session_key] = str(region.pk) if region else None
        request.session.save()

        # Redirect the user to the next page (usually set to the page the
        # user came from).
        next_path = self.request.POST.get('next')
        if not (next_path and is_safe_url(next_path, request.get_host())):
            next_path = reverse('home.home')
        return redirect(next_path)


class ToggleSubregions(View):
    """
    Update session variable that manages whether to include data for
    sub-regions or only the current region.
    """

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if 'include_subregions' not in request.POST:
            return HttpResponseBadRequest(
                "Request data should include `include_subregions`.")

        # Determine whether to include sub-regions and store the value
        # in the session.
        val = request.POST.get('include_subregions')
        if val in ('0', '1'):
            val = bool(int(val))
            request.session['include_subregions'] = val
            request.session.save()
            if val:
                msg = "Now showing data from {region} and its sub-regions."
            else:
                msg = "Showing data from {region} only."
            messages.info(request, msg.format(region=request.region))
        else:
            return HttpResponseBadRequest(
                "`include_subregions` should be either '0' or '1'.")

        # Redirect the user to the next page (usually set to the page the
        # user came from).
        next_path = request.POST.get('next')
        if not (next_path and is_safe_url(next_path, request.get_host())):
            next_path = reverse("home.home")
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
                    Contact.objects.active(),
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


class BoundaryListView(ListView):

    def get(self, request, *args, **kwargs):
        try:
            boundary = Boundary.objects.get(id=self.kwargs['boundary'])
        except Boundary.DoesNotExist:
                return HttpResponseBadRequest()

        return HttpResponse(
            json.dumps(boundary.as_geojson()),
            content_type='application/json')
