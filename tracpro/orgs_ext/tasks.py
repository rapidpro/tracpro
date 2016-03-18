from __future__ import unicode_literals

import datetime

from celery import signature
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.timezone import now as get_now

from djcelery_transactions import PostTransactionTask

from temba_client.base import TembaAPIError
from temba_client.utils import parse_iso8601, format_iso8601

from tracpro.celery import app as celery_app

from . import utils


logger = get_task_logger(__name__)

LAST_RUN_KEY = 'last_run_time:{task}:{org}'

ORG_TASK_LOCK = 'org_task:{task}:{org}'

LOCK_EXPIRE = (settings.ORG_TASK_TIMEOUT * 12).seconds


class ScheduleTaskForActiveOrgs(PostTransactionTask):

    def apply_async(self, *args, **kwargs):
        kwargs.setdefault('queue', 'org_scheduler')
        kwargs.setdefault('expires', datetime.datetime.now() + settings.ORG_TASK_TIMEOUT)
        return super(ScheduleTaskForActiveOrgs, self).apply_async(*args, **kwargs)

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
                signature(task_name, args=[org.pk]).delay()
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

    def acquire_lock(self, org):
        key = ORG_TASK_LOCK.format(task=self.__name__, org=org.pk)
        return cache.add(key, 'true', LOCK_EXPIRE)

    def apply_async(self, *args, **kwargs):
        kwargs.setdefault('expires', datetime.datetime.now() + settings.ORG_TASK_TIMEOUT)
        time_limit = settings.ORG_TASK_TIMEOUT.seconds
        kwargs.setdefault('time_limit', time_limit + 15)
        kwargs.setdefault('soft_time_limit', time_limit)
        kwargs.setdefault('max_retries', 0)
        return super(OrgTask, self).apply_async(*args, **kwargs)

    def check_rate_limit(self, org):
        """Return True if the task has been run too recently for this org."""
        now = get_now()
        last_run_key = LAST_RUN_KEY.format(task=self.__name__, org=org.pk)
        last_run_time = cache.get(last_run_key)
        if last_run_time is not None:
            last_run_time = parse_iso8601(last_run_time)
            if now - last_run_time < settings.ORG_TASK_TIMEOUT:
                return True
        cache.set(last_run_key, format_iso8601(now))
        return False

    def release_lock(self, org):
        key = ORG_TASK_LOCK.format(task=self.__name__, org=org.pk)
        return cache.delete(key)

    def run(self, org_pk):
        """Run the org_task with locks and logging."""
        org = apps.get_model('orgs', 'Org').objects.get(pk=org_pk)
        if self.acquire_lock(org):
            try:
                if self.check_rate_limit(org):
                    logger.info(
                        "{}: Skipping task for {} because rate limit "
                        "was exceeded.".format(
                            self.__name__, org.name))
                    return None

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
                else:
                    logger.info(
                        "{}: Finished task for {}.".format(self.__name__, org.name))
                    return result

            except SoftTimeLimitExceeded:
                msg = "{}: Time limit exceeded for {}".format(self.__name__, org.name)
                logger.error(msg)

                # FIXME: Logging is not sending us this error email.
                send_mail(
                    subject="{} {}".format(settings.EMAIL_SUBJECT_PREFIX, msg),
                    message=msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=dict(settings.ADMINS).values(),
                    fail_silently=True)

            finally:
                self.release_lock(org)
        logger.info(
            "{}: Skipping task for {} because the task is already "
            "running for this org.".format(self.__name__, org.name))
        return None
