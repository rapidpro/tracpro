from django import template


register = template.Library()


@register.inclusion_tag("polls/_filters_field.html")
def field(form, field_name, **kwargs):
    kwargs.update({
        'form': form,
        'field': form[field_name],
    })
    return kwargs
