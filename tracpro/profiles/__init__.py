from __future__ import absolute_import, unicode_literals

from dash.utils import get_obj_cacheable

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from tracpro.groups.models import Region


# === Monkey patching for the User class === #

def _user_create(cls, org, full_name, email, password, change_password=False,
                 regions=None, **kwargs):
    """
    Creates a regular user with specific region access
    """
    from .models import Profile

    # create auth user
    user = cls.objects.create(is_active=True, username=email, email=email, **kwargs)
    user.set_password(password)
    user.save()

    # add profile
    Profile.objects.create(user=user, full_name=full_name, change_password=change_password)

    # setup as org editor with limited region access
    if org:
        user.org_editors.add(org)
    if regions:
        user.update_regions(regions)
    return user


def _user_clean(user):
    # we use email for login
    if User.objects.filter(email=user.email).exclude(pk=user.pk).exists():
        raise ValidationError(_("Email address already taken."))
    user.username = user.email
    super(User, user).clean()


def _user_has_profile(user):
    from .models import Profile
    try:
        return bool(user.profile)
    except Profile.DoesNotExist:
        return False


def _user_get_full_name(user):
    """
    Override regular get_full_name which returns first_name + last_name
    """
    if user.has_profile():
        return user.profile.full_name
    return super(User, user).get_full_name()


def _user_get_direct_regions(user, org):
    """Return org regions user has direct permission for."""
    def calculate():
        # org admins have implicit access to all regions
        if user.is_admin_for(org):
            return Region.get_all(org)
        else:
            return user.regions.filter(is_active=True)
    attr_name = '_regions_{}'.format(org.pk)  # cache per org
    return get_obj_cacheable(user, attr_name, calculate)


def _user_get_all_regions(user, org):
    """Return org regions user has direct or implied (by hierarchy) permission for."""
    def calculate():
        regions = user.get_direct_regions(org).get_descendants(include_self=True)
        regions = regions.filter(is_active=True)
        return regions
    attr_name = '_regions_with_descendants_{}'.format(org.pk)  # cache per org
    return get_obj_cacheable(user, attr_name, calculate)


def _user_update_regions(user, regions):
    """
    Updates a user's regions
    """
    user.regions.clear()
    user.regions.add(*regions)

    for org_name in set(region.org.name for region in regions):
        for attr in ('_regions_with_descendants_{}', '_regions_{}'):
            if hasattr(user, attr.format(org_name)):
                delattr(user, attr.format(org_name))


def _user_has_region_access(user, region):
    """Whether the user can access the region.

    The user can either access the region directly, or one of its parents.
    """
    if user.is_superuser or user.is_admin_for(region.org):
        return True
    else:
        pks = region.get_ancestors(include_self=True).values_list('pk')
        return user.regions.filter(pk__in=pks).exists()


def _user_is_admin_for(user, org):
    """
    Whether this user is an administrator for the given org
    """
    return org.administrators.filter(pk=user.pk).exists()


def _user_unicode(user):
    if user.has_profile():
        if user.profile.full_name:
            return user.profile.full_name
    else:
        return user.username  # superuser

    return user.email or user.username


User.add_to_class('create', classmethod(_user_create))
User.add_to_class('clean', _user_clean)
User.add_to_class('has_profile', _user_has_profile)
User.add_to_class('get_full_name', _user_get_full_name)
User.add_to_class('get_direct_regions', _user_get_direct_regions)
User.add_to_class('get_all_regions', _user_get_all_regions)
User.add_to_class('update_regions', _user_update_regions)
User.add_to_class('has_region_access', _user_has_region_access)
User.add_to_class('is_admin_for', _user_is_admin_for)
User.add_to_class('__unicode__', _user_unicode)
User.add_to_class('__str__', _user_unicode)
