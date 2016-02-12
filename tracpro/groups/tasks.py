from djcelery_transactions import task

from django.apps import apps

from tracpro.orgs_ext.tasks import OrgTask


@task
class FetchOrgBoundaries(OrgTask):

    def org_task(self, org):
        """
        Fetches new and modified boundaries for the given org and creates/updates.
        """
        from .models import Boundary

        Boundary.fetch_boundaries(org)


@task
class SyncOrgBoundaries(OrgTask):

    def org_task(self, org):
        apps.get_model('groups', 'Boundary').objects.sync(org)
