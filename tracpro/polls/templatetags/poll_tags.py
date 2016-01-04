from django import template


register = template.Library()


@register.inclusion_tag("polls/filter_fieldset.html")
def fieldset(form, *fields):
    return {
        'fields': [form[field] for field in fields],
    }
