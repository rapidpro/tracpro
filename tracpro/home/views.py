from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartTemplateView
from tracpro.groups.models import Group, Region
from tracpro.polls.models import Poll


class HomeView(OrgPermsMixin, SmartTemplateView):
    """
    TracPro homepage
    """
    title = _("Home")
    template_name = 'home/home.haml'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        if 'region' in self.kwargs:
            try:
                region = self.request.user_regions.get(pk=self.kwargs['region'])
            except Region.DoesNotExist:
                raise PermissionDenied()
        else:
            region = self.request.user_regions.first()

        if self.request.region:
            latest_issues = self.request.region.issues.order_by('-conducted_on')[0:3]
            context['latest_issues'] = latest_issues

        context['all_groups'] = Group.get_all(self.request.org).order_by('name')
        return context
