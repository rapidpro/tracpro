from django import template

from .. import utils


register = template.Library()


@register.inclusion_tag("charts/filter_field.html")
def filter_field(form, field_name, **kwargs):
    kwargs.update({
        'form': form,
        'field': form[field_name],  # accesses the BoundField.
    })
    return kwargs


@register.filter
def chart_json(data):
    return utils.render_data(data)
