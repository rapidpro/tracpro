

def user_is_admin(request):
    org = request.org
    is_admin = org and request.user.is_authenticated() and request.user.is_admin_for(org)
    return {
        'user_is_admin': is_admin,
    }
