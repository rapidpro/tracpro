from __future__ import unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from dash.orgs.models import Org

from tracpro.contacts.models import DataField
from tracpro.polls.models import Answer, Question


@receiver(post_save, sender=Org)
def set_visible_data_fields(sender, instance, **kwargs):
    """Hook to update the visible DataFields for an org."""
    if hasattr(instance, '_visible_data_fields'):
        keys = instance._visible_data_fields.values_list('key', flat=True)
        DataField.objects.set_active_for_org(instance, keys)


@receiver(post_save, sender=Org)
def set_value_to_use(sender, instance, **kwargs):
    """
    Hook to update 'value_to_use' in numeric answers based on how_to_handle_sameday_responses.
    Unfortunately we can't do this in the form.save() method because the admin doesn't commit
    the save until later.
    """
    for answer in Answer.objects.filter(
        question__poll__org=instance,
        question__question_type=Question.TYPE_NUMERIC,
    ).distinct():
        answer.update_own_sameday_values_and_others()
