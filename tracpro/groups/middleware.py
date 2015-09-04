from __future__ import absolute_import, unicode_literals

from tracpro.groups.models import Region


class UserRegionsMiddleware(object):

    def get_region(self, request, user_regions, region_id):
        """Try to retrieve the specified region from the user's regions."""
        region = user_regions.filter(pk=region_id).first()
        if not region:
            if request.user.is_authenticated() and request.org:
                if not request.user.is_admin_for(request.org):
                    # Only org admins may see "All Regions."
                    region = user_regions.first()
        return region

    def process_request(self, request):
        # Whether or not sub-region data should be included.
        request.include_subregions = request.session.get('include_subregions', True)

        # Determine the org regions the user has access to.
        if request.org and request.user.is_authenticated():
            request.user_regions = request.user.get_all_regions(request.org)
        else:
            request.user_regions = Region.objects.none()

        if '_region' in request.GET:
            # Update current region information stored in the session.
            try:
                region_id = int(request.GET['_region'])
            except ValueError:
                region_id = None

            request.region = self.get_region(request, request.user_regions, region_id)
            request.session['region'] = request.region.pk if request.region else None
        else:
            # Retrieve current region information from the session.
            region_id = request.session.get('region', None)
            request.region = self.get_region(request, request.user_regions, region_id)

            # Set it back in the session in case this is the first request
            # or the old region is no longer valid.
            request.session['region'] = request.region.pk if request.region else None

        # Calculate which org regions to retrieve data for.
        if request.region:
            if request.include_subregions:
                request.data_regions = request.region.get_descendants(include_self=True)
                request.data_regions = request.data_regions.filter(pk__in=request.user_regions)
            else:
                request.data_regions = [request.region]
        else:
            request.data_regions = None
