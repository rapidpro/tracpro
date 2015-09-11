from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin

from django.utils.translation import ugettext_lazy as _

from smartmin.users.views import SmartTemplateView

from tracpro.polls.models import Poll
from tracpro.baseline.models import BaselineTerm
from tracpro.baseline.utils import chart_baseline


class HomeView(OrgPermsMixin, SmartTemplateView):
    """TracPro homepage"""

    title = _("Home")
    template_name = 'home/home.html'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['polls'] = Poll.get_all(self.request.org).order_by('name')

        # Loop through all baseline terms, until we find one with data
        for baselineterm in BaselineTerm.objects.all().order_by('-end_date'):
            data_found = baselineterm.check_for_data(self.request.data_regions)
            if data_found:
                answers_dict, baseline_dict, all_regions, date_list = chart_baseline(
                    baselineterm=baselineterm, regions=self.request.data_regions, region_selected=0)
                context['all_regions'] = all_regions
                context['date_list'] = date_list
                context['baseline_dict'] = baseline_dict
                context['answers_dict'] = answers_dict
                context['baselineterm'] = baselineterm
                break  # Found our baseline chart with data, send it back to the view

        return context
