from __future__ import absolute_import, unicode_literals


class UserRegionsMiddleware(object):

    def process_request(self, request):
        """Store commonly-used region variables on the request."""
        self.set_user_regions(request)
        self.set_include_subregions(request)
        self.set_region(request)
        self.set_data_regions(request)

    def set_user_regions(self, request):
        # Determine the org regions the user has access to.
        if request.org and request.user.is_authenticated():
            request.user_regions = request.user.get_all_regions(request.org)
        else:
            request.user_regions = None

    def set_include_subregions(self, request):
        # Whether or not sub-region data should be included.
        request.include_subregions = request.session.get('include_subregions', True)

    def set_region(self, request):
        # Find the currently-active region.
        if request.org and request.user.is_authenticated():
            region_id = request.session.get(
                '{org}:region_id'.format(org=request.org.pk))
            region = request.user_regions.filter(pk=region_id).first()
            if not region and not request.user.is_admin_for(request.org):
                # Only org admins may see "All Regions".
                region = request.user_regions.first()
            request.region = region
        else:
            request.region = None

    def set_data_regions(self, request):
        # Calculate which org regions to retrieve data for.
        if request.region:
            if request.include_subregions:
                request.data_regions = request.region.get_descendants(include_self=True)
                request.data_regions = request.data_regions.filter(pk__in=request.user_regions)
            else:
                request.data_regions = [request.region]
        else:
            request.data_regions = None
