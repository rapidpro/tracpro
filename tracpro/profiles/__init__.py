from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from tracpro.groups.models import Region
from .models import Profile


######################### Monkey patching for the User class #########################

def _user_create(cls, org, full_name, email, password, change_password=False, regions=()):
    """
    Creates a regular user with specific region access
    """
    # create auth user
    user = cls.objects.create(is_active=True, username=email, email=email)
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
    try:
        return bool(user.profile)
    except Profile.DoesNotExist:
        return False


def _user_get_full_name(user):
    """
    Override regular get_full_name which returns first_name + last_name
    """
    return user.profile.full_name if user.has_profile() else " ".join([user.first_name, user.last_name]).strip()


def _user_get_regions(user, org):
    if not hasattr(user, '_regions'):
        # org admins have implicit access to all regions
        if user.is_admin_for(org):
            user._regions = Region.get_all(org)
        else:
            user._regions = user.regions.filter(is_active=True)

    return user._regions


def _user_update_regions(user, regions):
    """
    Updates a user's regions
    """
    user.regions.clear()
    user.regions.add(*regions)


def _user_has_region_access(user, region):
    """
    Whether the given user has access to the given region
    """
    if user.is_superuser or user.is_admin_for(region.org):
        return True
    else:
        return user.regions.filter(pk=region.pk).exists()


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


User.create = classmethod(_user_create)
User.clean = _user_clean
User.has_profile = _user_has_profile
User.get_full_name = _user_get_full_name
User.get_regions = _user_get_regions
User.update_regions = _user_update_regions
User.has_region_access = _user_has_region_access
User.is_admin_for = _user_is_admin_for
User.__unicode__ = _user_unicode
