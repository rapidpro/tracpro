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

        # TODO: create a utils.py utility function in baseline app and call that here
        # and there
        """
        # Loop through all baseline terms, until we find one with data
        for baselineterm in BaselineTerm.objects.all().order_by('-end_date'):
            baseline_dict, baseline_dates = baselineterm.get_baseline(region=None)
            if baseline_dict:
                follow_ups, dates = baselineterm.get_follow_up(region=None)
                # Create a list of all dates for this poll
                # Example: date_list =  ['09/01', '09/02', '09/03', ...]
                date_list = []
                for date in dates:
                    date_formatted = date.strftime('%m/%d')
                    date_list.append(date_formatted)
                context['date_list'] = date_list

        """

        return context
