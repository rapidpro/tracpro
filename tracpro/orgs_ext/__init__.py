from __future__ import absolute_import, unicode_literals

import json

from dash.orgs.models import Org
from dash.utils import random_string


######################### Monkey patching for the Org class #########################

ORG_CONFIG_SECRET_TOKEN = 'secret_token'


def _org_get_secret_token(org):
    return org.get_config(ORG_CONFIG_SECRET_TOKEN)


def _org_clean(org):
    super(Org, org).clean()

    # set config defaults
    if not org.config:
        org.config = json.dumps({ORG_CONFIG_SECRET_TOKEN: random_string(16).lower()})


Org.get_secret_token = _org_get_secret_token
Org.clean = _org_clean
