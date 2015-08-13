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

    def clean(self, *args, **kwargs):
        cleaned_data = super(BaselineTermForm, self).clean()
        import ipdb; ipdb.set_trace();

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date > end_date:
            raise forms.ValidationError(
                    "Start date should be before end date."
                )

        baseline_question = cleaned_data.get("baseline_question")
        follow_up_question = cleaned_data.get("follow_up_question")

        if baseline_question.id == follow_up_question.id:
            raise forms.ValidationError(
                    "Baseline question and follow up question should be different."
                )

        return cleaned_data
