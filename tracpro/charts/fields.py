from django import forms
from django.utils.translation import ugettext_lazy as _

from . import utils


class FilterDateField(forms.DateTimeField):
    widget = forms.widgets.DateInput
    default_error_messages = {
        'invalid': _("Please enter a valid date."),
    }

    def widget_attrs(self, widget):
        attrs = super(FilterDateField, self).widget_attrs(widget)
        attrs['class'] = (attrs.get('class', '') + ' datepicker').strip()
        return attrs

    def clean(self, value):
        """Convert to a datetime representing midnight of the requested date."""
        value = super(FilterDateField, self).clean(value)
        return utils.midnight(value) if value is not None else None
