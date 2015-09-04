from mptt import forms as mptt

from django.db.models import Min
from django.utils.html import conditional_escape, mark_safe


class ModifiedLevelTreeNodeChoiceField(mptt.TreeNodeChoiceField):
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
        super(ModifiedLevelTreeNodeChoiceField, self)._set_queryset(queryset)
        self.highest_level = queryset.aggregate(Min('level'))['level__min']

    queryset = property(mptt.TreeNodeChoiceField._get_queryset, _set_queryset)
