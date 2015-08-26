from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin

from django.utils.translation import ugettext_lazy as _

from smartmin.users.views import SmartTemplateView

from tracpro.polls.models import Poll


class HomeView(OrgPermsMixin, SmartTemplateView):
    """TracPro homepage"""

    title = _("Home")
    template_name = 'home/home.html'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['polls'] = Poll.get_all(self.request.org).order_by('name')
        return context
