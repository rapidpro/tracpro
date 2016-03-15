from __future__ import unicode_literals

import json

from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache

from .utils import OrgConfigField


class DashOrgConfig(AppConfig):
    # Must override config for dash.orgs or else Org model won't be available.
    name = "dash.orgs"

    def ready(self):
        """Monkey patching for the orgs.Org class."""
        from . import signals  # noqa

        Org = self.get_model('Org')

        def _org_get_task_result(org, task_type):
            cache_key = Org.LAST_TASK_CACHE_KEY % (org.pk, task_type.name)
            result = cache.get(cache_key)
            return json.loads(result) if result is not None else None

        def _org_set_task_result(org, task_type, result):
            cache_key = Org.LAST_TASK_CACHE_KEY % (org.pk, task_type.name)
            cache.set(cache_key, json.dumps(result), Org.LAST_TASK_CACHE_TTL)

        Org.add_to_class('LAST_TASK_CACHE_KEY', 'org:%d:task_result:%s')
        Org.add_to_class('LAST_TASK_CACHE_TTL', 60 * 60 * 24 * 7)  # 1 week

        Org.add_to_class('get_task_result', _org_get_task_result)
        Org.add_to_class('set_task_result', _org_set_task_result)

        # Never set config directly;
        # allow config attributes to be set as if they were normal attributes.
        for config_field in settings.ORG_CONFIG_FIELDS:
            name = config_field['name']
            Org.add_to_class(name, OrgConfigField(name))
