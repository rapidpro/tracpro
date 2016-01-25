from django import template


register = template.Library()


@register.inclusion_tag("filters/field.html")
def field(form, field_name, **kwargs):
    kwargs.update({
        'form': form,
        'field': form[field_name],
    })
    return kwargs
