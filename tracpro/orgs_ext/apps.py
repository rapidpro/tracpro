import json

from django.apps import AppConfig
from django.core.cache import cache
from django.utils.functional import cached_property


class settable_cached_property(cached_property):
    """
    Extension of Django's cached_property decorator class that also allows
    the value of the property to be set.
    """

    def __init__(self, get_func, set_func, name=None):
        self.set_func = set_func
        super(settable_cached_property, self).__init__(get_func, name)

    def __set__(self, instance, value):
        self.set_func(instance, value)


class DashOrgConfig(AppConfig):
    # Must override config for dash.orgs or else Org model won't be available.
    name = "dash.orgs"

    def ready(self):
        """Monkey patching for the orgs.Org class."""
        Org = self.get_model('Org')

        def _org_clean(org):
            """Set a default facility code."""
            super(org.__class__, org).clean()
            if not org.facility_code_field:
                org.facility_code_field = 'facility_code'

        def _org_get_available_languages(org):
            return org.get_config('available_languages') or []

        def _org_get_facility_code_field(org):
            return org.get_config('facility_code_field')

        def _org_get_task_result(org, task_type):
            cache_key = Org.LAST_TASK_CACHE_KEY % (org.pk, task_type.name)
            result = cache.get(cache_key)
            return json.loads(result) if result is not None else None

        def _org_set_available_languages(org, value):
            return org.set_config('available_languages', value, commit=False)

        def _org_set_facility_code_field(org, value):
            return org.set_config('facility_code_field', value, commit=False)

        def _org_set_task_result(org, task_type, result):
            cache_key = Org.LAST_TASK_CACHE_KEY % (org.pk, task_type.name)
            cache.set(cache_key, json.dumps(result), Org.LAST_TASK_CACHE_TTL)

        Org.add_to_class('LAST_TASK_CACHE_KEY', 'org:%d:task_result:%s')
        Org.add_to_class('LAST_TASK_CACHE_TTL', 60 * 60 * 24 * 7)  # 1 week

        Org.add_to_class('clean', _org_clean)
        Org.add_to_class('get_available_languages', _org_get_available_languages)
        Org.add_to_class('get_facility_code_field', _org_get_facility_code_field)
        Org.add_to_class('get_task_result', _org_get_task_result)
        Org.add_to_class('set_available_languages', _org_set_available_languages)
        Org.add_to_class('set_facility_code_field', _org_set_facility_code_field)
        Org.add_to_class('set_task_result', _org_set_task_result)

        # Never set config directly;
        # allow config attributes to be set as if they were properties.
        Org.add_to_class('available_languages', settable_cached_property(
            _org_get_available_languages,
            _org_set_available_languages,
        ))
        Org.add_to_class('facility_code_field', settable_cached_property(
            _org_get_facility_code_field,
            _org_set_facility_code_field,
        ))
