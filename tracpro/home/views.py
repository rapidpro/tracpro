from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin

from django.utils.translation import ugettext_lazy as _

from smartmin.views import SmartTemplateView

from tracpro.baseline.charts import chart_baseline
from tracpro.baseline.forms import BaselineTermFilterForm
from tracpro.baseline.models import BaselineTerm
from tracpro.polls.models import Poll


class HomeView(OrgPermsMixin, SmartTemplateView):
    """TracPro homepage"""

    title = _("Home")
    template_name = 'home/home.html'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        polls = Poll.objects.active().by_org(self.request.org)
        polls = polls.order_by('name')

        indicators = BaselineTerm.objects.by_org(self.request.org)
        indicators = indicators.order_by('-end_date')
        indicators = indicators[0:5]

        # Chart baseline data for the most recent indicator that has
        # follow-up data.
        featured_indicator = None
        chart_data = None
        for indicator in indicators:
            pollruns, responses, answers = indicator.get_follow_up_data()
            if answers.exists():
                featured_indicator = indicator
                # Construct a default form for filtering baseline data.
                filter_form = BaselineTermFilterForm(
                    org=self.request.org,
                    baseline_term=indicator,
                    data_regions=self.request.data_regions)
                filter_form.full_clean()
                chart_data, summary_table = chart_baseline(
                    indicator, filter_form, self.request.region,
                    self.request.include_subregions)
                break

        kwargs.setdefault('featured_indicator', featured_indicator)
        kwargs.setdefault('chart_data', chart_data)
        kwargs.setdefault('polls', polls)
        kwargs.setdefault('recent_indicators', indicators)
        return super(HomeView, self).get_context_data(**kwargs)
