from __future__ import unicode_literals


def show_subregions_toggle_form(request):
    show = False
    if request.region:
        if any(c in request.user_regions for c in request.region.get_descendants()):
            show = True
    return {
        'show_subregions_toggle_form': show,
    }
