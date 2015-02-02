from __future__ import absolute_import, unicode_literals

from tracpro.groups.models import Region


class UserRegionsMiddleware(object):
    """
    Middleware to set region
    """
    def process_request(self, request):
        if request.org and not request.user.is_anonymous():
            user_regions = request.user.get_regions(request.org).order_by('name')

            if '_region' in request.GET:
                region_id = request.GET.get('_region', None)
                request.session['region'] = region_id
            elif 'region' in request.session:
                region_id = request.session['region']
            else:
                region_id = None

            if region_id:
                region = user_regions.filter(pk=region_id).first()
            else:
                region = user_regions.first()

        else:
            user_regions = Region.objects.none()
            region = None

        request.user_regions = user_regions
        request.region = region
