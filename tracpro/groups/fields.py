from mptt import forms as mptt

from django.db.models import Min
from django.utils.html import conditional_escape, mark_safe


class ModifiedLevelMixin(object):
    """Offsets the level indicator relative to the highest level in the queryset.

    Turns this:

        ---- Uganda
        ------ Kampala
        ------ Entebbe

    into this:

        Uganda
        -- Kampala
        -- Entebbe

    """

    def _get_level_indicator(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr) - self.highest_level
        return mark_safe(conditional_escape(self.level_indicator) * level)

    def _set_queryset(self, queryset):
        """Set the highest level when the queryset is set."""
        super(ModifiedLevelMixin, self)._set_queryset(queryset)
        self.highest_level = queryset.aggregate(Min('level'))['level__min']


class ModifiedLevelTreeNodeChoiceField(ModifiedLevelMixin, mptt.TreeNodeChoiceField):
    queryset = property(
        mptt.TreeNodeChoiceField._get_queryset,
        ModifiedLevelMixin._set_queryset)


class ModifiedLevelTreeNodeMultipleChoiceField(ModifiedLevelMixin, mptt.TreeNodeMultipleChoiceField):
    queryset = property(
        mptt.TreeNodeMultipleChoiceField._get_queryset,
        ModifiedLevelMixin._set_queryset)
