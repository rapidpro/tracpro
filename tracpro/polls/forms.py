from django import forms
from django.utils.translation import ugettext_lazy as _

from dash.utils import get_month_range

from tracpro.charts import filters

from . import models


class PollForm(forms.ModelForm):

    class Meta:
        model = models.Poll
        fields = ('name',)


class QuestionForm(forms.ModelForm):

    class Meta:
        model = models.Question
        fields = ('name', 'question_type', 'is_active')


QuestionFormSet = forms.modelformset_factory(
    models.Question,
    form=QuestionForm,
    extra=0,
    can_delete=False)


class ActivePollsForm(forms.Form):
    """Set which polls should be synced with RapidPro."""
    polls = forms.ModelMultipleChoiceField(
        queryset=None, required=False, label=_("Active flows"),
        help_text=_("Flows to track as polls."))

    def __init__(self, org, *args, **kwargs):
        self.org = org
        super(ActivePollsForm, self).__init__(*args, **kwargs)

        # Make sure we have the most up-to-date Poll info.
        # NOTE: This makes an in-band request to an external API.
        models.Poll.objects.sync(self.org)

        polls = models.Poll.objects.by_org(self.org)
        self.fields['polls'].queryset = polls
        self.fields['polls'].initial = polls.active()

    def save(self):
        uuids = self.cleaned_data['polls'].values_list('flow_uuid', flat=True)
        models.Poll.objects.set_active_for_org(self.org, uuids)


class PollChartFilterForm(filters.DateRangeFilter, filters.DataFieldFilter,
                          filters.FilterForm):
    NUMERIC_DATA_CHOICES = (
        ('', ''),
        ('sum', _("Sum of responses")),
        ('average', _("Average of responses")),
        ('response-rate', _("Response rate")),
    )

    numeric = forms.ChoiceField(
        label=_("Numeric display"),
        help_text=_("How responses to numeric questions will be charted."),
        choices=NUMERIC_DATA_CHOICES)
    split_regions = forms.BooleanField(
        required=False,
        help_text=_("Split out regional data for numeric charts."))

    def __init__(self, *args, **kwargs):
        if not kwargs.get('data'):
            # Set valid data if None (or {}) was provided.
            # Form will always be considered bound.
            start_date, end_date = get_month_range()
            kwargs['data'] = {
                'numeric': 'sum',
                'date_range': 'month',
                'start_date': start_date,
                'end_date': end_date,
                'split_regions': False,
            }
        super(PollChartFilterForm, self).__init__(*args, **kwargs)


class PollRunChartFilterForm(filters.DataFieldFilter, filters.FilterForm):
    pass
