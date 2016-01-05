from django import template


register = template.Library()


@register.inclusion_tag("polls/_filters_fieldset.html")
def fieldset(form, *fields, **kwargs):
    field_count = len(fields)
    col_width = 12 / field_count
    label_width = kwargs.pop('label_width', (2, 4, 6, 12)[field_count])
    field_width = 12 - label_width

    bound_fields = []
    for name in fields:
        field = form[name]
        field.col_width = col_width
        field.label_width = label_width
        field.field_width = field_width
        bound_fields.append(field)

    kwargs.update({
        'form': form,
        'fields': bound_fields,
    })
    return kwargs
