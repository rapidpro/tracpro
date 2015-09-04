from __future__ import absolute_import, unicode_literals

from tracpro.groups.models import Region


class UserRegionsMiddleware(object):
    """
    Middleware to set region
    """
    def process_request(self, request):
        region = None

        if request.org and not request.user.is_anonymous():
            user_regions = request.user.get_direct_regions(request.org).order_by('name')

            if '_region' in request.GET:
                region_id = int(request.GET['_region'])
            elif 'region' in request.session:
                region_id = request.session['region']
            else:
                region_id = None

            # user requested a specific region...
            if region_id:
                region = user_regions.filter(pk=region_id).first()
            else:
                region = None

            # can't choose All Regions unless you're an admin
            if not region and not request.user.is_admin_for(request.org):
                region = user_regions.first()

            request.session['region'] = region.pk if region else None
        else:
            user_regions = Region.objects.none()

        # save on the request object for convenience
        request.user_regions = user_regions
        request.region = region
