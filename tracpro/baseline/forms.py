from django import forms

from .models import BaselineTerm


class BaselineTermForm(forms.ModelForm):
    """
    Form for Baseline Term
    """
    class Meta:
        model = BaselineTerm
        fields = ('name', 'org', 'start_date', 'end_date',
                  'baseline_poll', 'baseline_question',
                  'follow_up_poll', 'follow_up_question')

        widgets = {
            'start_date': forms.widgets.DateInput(attrs={'class': 'datepicker'}),
            'end_date': forms.widgets.DateInput(attrs={'class': 'datepicker'}),
            'org': forms.HiddenInput()
        }
