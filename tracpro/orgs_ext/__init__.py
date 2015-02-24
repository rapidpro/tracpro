from __future__ import absolute_import, unicode_literals

import json

from dash.orgs.models import Org
from django.core.cache import cache
from enum import Enum


class TaskType(Enum):
    sync_contacts = 1
    fetch_runs = 2


LAST_TASK_CACHE_KEY = 'org:%d:task_result:%s'
LAST_TASK_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week


######################### Monkey patching for the Org class #########################

ORG_CONFIG_FACILITY_CODE_FIELD = 'facility_code_field'


def _org_get_facility_code_field(org):
    return org.get_config(ORG_CONFIG_FACILITY_CODE_FIELD)


def _org_get_task_result(org, task_type):
    result = cache.get(LAST_TASK_CACHE_KEY % (org.pk, task_type.name))
    return json.loads(result) if result is not None else None


def _org_set_task_result(org, task_type, result):
    cache.set(LAST_TASK_CACHE_KEY % (org.pk, task_type.name), json.dumps(result), LAST_TASK_CACHE_TTL)


def _org_clean(org):
    super(Org, org).clean()

    # set config defaults
    if not org.config:
        org.config = json.dumps({ORG_CONFIG_FACILITY_CODE_FIELD: 'facility_code'})


Org.get_facility_code_field = _org_get_facility_code_field
Org.get_task_result = _org_get_task_result
Org.set_task_result = _org_set_task_result