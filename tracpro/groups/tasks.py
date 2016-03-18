from __future__ import unicode_literals

from djcelery_transactions import task

from django.apps import apps

from tracpro.orgs_ext.tasks import OrgTask


@task
class SyncOrgBoundaries(OrgTask):

    def org_task(self, org):
        apps.get_model('groups', 'Boundary').objects.sync(org)
