from __future__ import unicode_literals

import datetime

from celery import signature
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from djcelery_transactions import PostTransactionTask

from temba_client.base import TembaAPIError
from temba_client.utils import parse_iso8601, format_iso8601

from tracpro.celery import app as celery_app

from . import utils


logger = get_task_logger(__name__)

FAILURE_COUNT = 'failure_count:{task}:{org}'

LAST_RUN_TIME = 'last_run_time:{task}:{org}'

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

    def apply_async(self, *args, **kwargs):
        kwargs.setdefault('expires', datetime.datetime.now() + settings.ORG_TASK_TIMEOUT)
        time_limit = settings.ORG_TASK_TIMEOUT.seconds
        kwargs.setdefault('time_limit', time_limit + 60)
        kwargs.setdefault('soft_time_limit', time_limit)
        kwargs.setdefault('max_retries', 0)
        return super(OrgTask, self).apply_async(*args, **kwargs)

    def _wrap_cache(self, method, org, key, *args, **kwargs):
        cache_key = key.format(task=self.__name__, org=org.pk)
        return getattr(cache, method)(cache_key, *args, **kwargs)

    def cache_add(self, *args, **kwargs):
        return self._wrap_cache("add", *args, **kwargs)

    def cache_delete(self, *args, **kwargs):
        return self._wrap_cache("delete", *args, **kwargs)

    def cache_get(self, *args, **kwargs):
        return self._wrap_cache("get", *args, **kwargs)

    def cache_incr(self, *args, **kwargs):
        return self._wrap_cache("incr", *args, **kwargs)

    def cache_set(self, *args, **kwargs):
        return self._wrap_cache("set", *args, **kwargs)

    def check_rate_limit(self, org):
        """Return the next run time if this task has run too recently."""
        now = timezone.now()

        last_run_time = self.cache_get(org, LAST_RUN_TIME)
        if last_run_time is not None:
            # Calculate how long until the task is eligible to run again.
            last_run_time = parse_iso8601(last_run_time)
            delta = settings.ORG_TASK_TIMEOUT * 2 ** self.cache_get(org, FAILURE_COUNT, 0)
            delta = max(delta, datetime.timedelta(days=1))
            if now - last_run_time < delta:
                return last_run_time + delta

        # Set the current time as the last run time and allow the task to run now.
        self.cache_set(org, LAST_RUN_TIME, format_iso8601(now))
        return None

    def fail_count_incr(self, org):
        """Increment the org's recorded failure count by 1."""
        self.cache_add(org, FAILURE_COUNT, 0)  # Set default value to 0.
        return self.cache_incr(org, FAILURE_COUNT)  # Increment value by 1.

    def fail_count_reset(self, org):
        """Reset the org's recorded failure count to 0."""
        self.cache_set(org, FAILURE_COUNT, 0)

    def lock_acquire(self, org):
        """Set a cache key that indicates the task is currently in progress.

        If the key is already set (task in progress), return False.
        """
        return self.cache_add(org, ORG_TASK_LOCK, 'true', LOCK_EXPIRE)

    def lock_release(self, org):
        """Delete cache key that indicates that this task is in progress."""
        self.cache_delete(org, ORG_TASK_LOCK)

    def run(self, org_pk):
        """Run the org_task with locks and logging."""
        org = apps.get_model('orgs', 'Org').objects.get(pk=org_pk)
        if self.lock_acquire(org):
            try:
                next_run_time = self.check_rate_limit(org)
                if next_run_time is not None:
                    logger.info(
                        "{}: Skipping task for {} because rate limit was "
                        "exceeded. Task will not be run again before {}.".format(
                            self.__name__, org.name, next_run_time))
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
                    self.fail_count_reset(org)
                    logger.info(
                        "{}: Finished task for {}.".format(
                            self.__name__, org.name))
                    return result

            except SoftTimeLimitExceeded:
                logger.debug(
                    "{}: Caught SoftTimeLimitExceeded exception for {}.".format(
                        self.__name__, org.name))

                fail_count = self.fail_count_incr(org)
                msg = "{}: Time limit exceeded (#{})for {}.".format(
                    self.__name__, fail_count, org.name)
                logger.error(msg)

                # FIXME: Logging is not sending us this error email.
                send_mail(
                    subject="{} {}".format(settings.EMAIL_SUBJECT_PREFIX, msg),
                    message=msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=dict(settings.ADMINS).values(),
                    fail_silently=True)

                logger.debug(
                    "{}: Finished processing SoftTimeLimitExceeded exception "
                    "for {}.".format(
                        self.__name__, org.name))
                return None

            except:
                fail_count = self.fail_count_incr(org)
                logger.info(
                    "{}: Unknown failure (#{}) for {}".format(
                        self.__name__, fail_count, org.name))
                raise

            finally:
                logger.debug(
                    "{}: Starting to release lock for {}.".format(
                        self.__name__, org.name))
                self.lock_release(org)
                logger.debug(
                    "{}: Released lock for {}.".format(
                        self.__name__, org.name))
        logger.info(
            "{}: Skipping task for {} because the task is already "
            "running for this org.".format(self.__name__, org.name))
        return None
