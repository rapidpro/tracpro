from __future__ import unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from dash.orgs.models import Org

from tracpro.contacts.models import DataField


@receiver(post_save, sender=Org)
def set_visible_data_fields(sender, instance, **kwargs):
    """Hook to update the visible DataFields for an org."""
    if hasattr(instance, '_visible_data_fields'):
        keys = instance._visible_data_fields.values_list('key', flat=True)
        DataField.objects.set_active_for_org(instance, keys)
