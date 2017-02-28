from __future__ import absolute_import, unicode_literals

import logging
import json

from dash.orgs.views import OrgPermsMixin

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Prefetch
from django.db.models.functions import Lower
from django.http import (
    HttpResponseBadRequest, HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from smartmin.views import SmartCRUDL, SmartListView, SmartFormView, SmartView

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
    actions = ('list', 'most_active', 'select', 'update_all')

    class List(OrgPermsMixin, SmartListView):
        fields = ('name', 'boundary', 'contacts')
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

        def get_context_data(self, **kwargs):
            org_boundaries = Boundary.objects.by_org(self.request.org)\
                .annotate(lcase_name=Lower('name')).order_by('lcase_name')
            kwargs.setdefault('org_boundaries', org_boundaries)
            return super(RegionCRUDL.List, self).get_context_data(**kwargs)

        def get_contacts(self, obj):
            return len(obj.prefetched_contacts)

        def get_boundary(self, obj):
            return obj.boundary.name if obj.boundary else "-"

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

    class UpdateAll(OrgPermsMixin, SmartView, View):
        http_method_names = ['post']

        @transaction.atomic
        def post(self, request, *args, **kwargs):
            """AJAX endpoint to update boundaries and hierarchy for all org regions."""
            org = request.org

            # Load data and validate that it is in the correct format.
            self.raw_data = request.POST.get('data', "").strip() or None
            try:
                data = json.loads(self.raw_data)
            except TypeError:
                return self.error(
                    "No data was provided in the `data` parameter.")
            except ValueError:
                return self.error(
                    "Data must be valid JSON.")
            if not isinstance(data, dict):
                return self.error(
                    "Data must be a dict that maps region id to "
                    "(parent id, boundary id).")
            if not all(isinstance(v, list) and len(v) == 2 for v in data.values()):
                return self.error(
                    "All data values must be of the format "
                    "(parent id, boundary id).")

            # Grab all of the org's regions and boundaries at once.
            regions = {str(r.pk): r for r in Region.get_all(org)}
            boundaries = {str(b.pk): b for b in Boundary.objects.by_org(org)}

            # Check that the user is updating exactly the regions from this
            # org, and that specified parents and boundaries are valid for
            # this org.
            valid_regions = set(regions.keys())
            valid_boundaries = set(boundaries.keys())
            sent_regions = set(str(i) for i in data.keys())
            sent_parents = set(str(i[0]) for i in data.values() if i[0] is not None)
            sent_boundaries = set(str(i[1]) for i in data.values() if i[1] is not None)
            if sent_regions != valid_regions:
                return self.error(
                    "Data must map region id to parent id for every region "
                    "in this org.")
            if not sent_parents.issubset(valid_regions):
                return self.error(
                    "Region parent must be a region from the same org, "
                    "or null.")
            if not sent_boundaries.issubset(valid_boundaries):
                return self.error(
                    "Region boundary must be a boundary from the same "
                    "org, or null.")

            # Re-set parent and boundary values for each region,
            # then rebuild the mptt tree.
            with Region.objects.disable_mptt_updates():
                for region_id, (parent_id, boundary_id) in data.items():
                    region = regions.get(str(region_id))
                    parent = regions.get(str(parent_id)) if parent_id else None
                    boundary = boundaries.get(str(boundary_id)) if boundary_id else None

                    changed = False
                    if region.boundary != boundary:
                        changed = True
                        self.log_change("boundary", region, region.boundary, boundary)
                        region.boundary = boundary
                    if region.parent != parent:
                        changed = True
                        self.log_change("parent", region, region.parent, parent)
                        region.parent = parent

                    if changed:
                        region.save()
            Region.objects.rebuild()

            return self.success("{} regions have been updated.".format(request.org))

        def log_change(self, name, region, old, new):
            message = "Updating {name} of {region} from {old} -> {new}.".format(
                name=name,
                region=region,
                old=old.name if old else None,
                new=new.name if new else None,
            )
            logger.debug("{} Regions: {}".format(self.request.org, message))

        def error(self, message):
            template = "{} Regions: {} {}"
            logger.warning(template.format(self.request.org, message, self.raw_data))
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': message,
            })

        def success(self, message):
            template = "{} Regions: {} {}"
            logger.info(template.format(self.request.org, message, self.raw_data))
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


class BoundaryCRUDL(SmartCRUDL):
    model = Boundary
    actions = ('list',)

    class List(OrgPermsMixin, SmartListView):

        def get_queryset(self):
            return Boundary.objects.by_org(self.request.org).order_by('-level')

        def render_to_response(self, context, **response_kwargs):
            results = {b.pk: b.as_geojson() for b in context['object_list']}
            return JsonResponse({'results': results})
