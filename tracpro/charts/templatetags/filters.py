from django import forms
from django import template

from .. import utils


register = template.Library()


@register.inclusion_tag("filters/field.html")
def field(form, field_name, **kwargs):
    kwargs.update({
        'form': form,
        'field': form[field_name],
    })
    return kwargs


@register.filter
def chart_json(data):
    return utils.render_data(data)


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)
