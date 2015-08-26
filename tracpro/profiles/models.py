from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    """Extension for the user class"""

    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    full_name = models.CharField(
        verbose_name=_("Full name"), max_length=128, null=True)
    change_password = models.BooleanField(
        default=False,
        help_text=_("User must change password on next login"))
