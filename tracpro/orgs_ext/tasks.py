from celery import signature
from celery.utils.log import get_task_logger

from django.apps import apps

from djcelery_transactions import task, PostTransactionTask

from temba_client.base import TembaAPIError

from tracpro.celery import app as celery_app

from . import utils


logger = get_task_logger(__name__)


@task
class ScheduleTaskForActiveOrgs(PostTransactionTask):

    def run(self, task_name):
        """Schedule the OrgTask to be run for each active org."""
        if task_name not in celery_app.tasks:
            logger.error(
                "{}: No task named '{}' is registered".format(
                    self.__name__, task_name))
            return

        logger.info(
            "{}: Starting to schedule {} for each active org.".format(
                self.__name__, task_name))
        for org in apps.get_model('orgs', 'Org').objects.all():
            if not org.is_active:
                logger.info(
                    "{}: Skipping {} for {} because it is not active.".format(
                        self.__name__, task_name, org.name))
            elif not org.api_token:
                logger.info(
                    "{}: Skipping {} for {} because it has no API token.".format(
                        self.__name__, task_name, org.name))
            else:
                signature(task_name, args=[org.pk]).delay()  # asynchronous
                logger.info(
                    "{}: Scheduled {} for {}.".format(
                        self.__name__, task_name, org.name))
        logger.info(
            "{}: Finished scheduling {} for each active org.".format(
                self.__name__, task_name))


class OrgTask(PostTransactionTask):
    """Scaffolding to CREATE a task that operates on a single org."""
    abstract = True

    def org_task(self, org):
        raise NotImplementedError("Class must define the action to take on the org.")

    def run(self, org_pk):
        """Run the org_task with appropriate logging."""
        org = apps.get_model('orgs', 'Org').objects.get(pk=org_pk)
        logger.info(
            "{}: Starting task for {}.".format(self.__name__, org.name))
        try:
            result = self.org_task(org)
        except TembaAPIError as e:
            if utils.caused_by_bad_api_key(e):
                logger.warning(
                    "{}: API token for {} is invalid.".format(
                        self.__name__, org.name), exc_info=True)
                return None
            else:
                raise
        logger.info(
            "{}: Finished task for {}.".format(self.__name__, org.name))
        return result
