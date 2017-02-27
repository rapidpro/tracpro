Changelog
=========

Tracpro's version is incremented upon each merge to master according to our
:ref:`production deployment process <release-to-production>`.

We recommend reviewing the release notes and code diffs before upgrading
between versions.

v1.5.0 (released 2017-02-27)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.5.0...develop

* Many-to-many contact to group relation update in the back-end
* Allow admins to set super user status on the front end
* Web interface to manage fetch runs

v1.4.3 (released 2016-04-06)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.4.2...develop

* Update docs structure.
* Remove outdated docs.
* Update deployment process notes.
* Reduce log level for "Scheduled task" message.
* Allow for custom templates and staticfiles directories.

v1.4.2 (released 2016-04-04)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.4.1...v1.4.2

* Reduce log levels

v1.4.1 (released 2016-03-29)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.4.0...v1.4.1

* Fix placement of lock release

v1.4.0 (released 2016-03-28)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.3.3...v1.4.0

* Migrations to move RapidPro uuid unique constraint to unique_together with
  another model field (`org` for Contact, Region, and Group models; `pollrun`
  for Response)

v1.3.3 (released 2016-03-28)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.3.2...v1.3.3

* Implement "backoff" for OrgTasks that fail
* Ensure that cache key timeout is set properly in OrgTask
* Do not use @task decorator on class-based task

v1.3.2 (released 2016-03-23)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.3.1...v1.3.2

* Add debug logging for OrgTask

v1.3.1 (released 2016-03-23)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.3.0...v1.3.1

* Fix formatting errors in this changelog
* Return `None` if `SoftTimeLimitExceeded` is raised during `OrgTask`
* Run `pipconflictchecker` on Travis builds
* Fail before running Travis tests if there are missing migrations
* Increase the `hard_time_limit` value for Org tasks

v1.3.0 (released 2016-03-22)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.2.1...v1.3.0

**Infrastructure**

* Update to Django==1.8.11
* Update versions on many third-party packages (excluding forks)
* Updated the Caktus smartmin fork
* Serve library scripts and stylesheets from `/static/libs/` rather than CDNs
* Ensure all test classes inherit from `TracProTest`, which ensures that critical features are mocked

**Features & Bugfixes**

* Fix email prefix on deployed environments
* Add `from __future__ import unicode_literals` to all files
* Only show responses from active contacts on charts for baseline, poll detail, and pollrun detail
* Don't abbreviate big numbers on charts (1,000,000 rather than 1M)
* Add user documentation about designing flows
* Add `Boundary` model to `tracpro.groups`
    * Sync with RapidPro
    * Add endpoint to retrieve all boundaries for an Org
* Add `boundary` foreign key to `Region` and allow setting the `boundary` on the Region list page
* Add contact data field filters to PollRun detail page & pass applicable filters to PollRun detail page when clicking on a data point on the Poll detail page.
* Store ruleset on the `Question` model
* Add ability to categorize arbitrary (numeric) values
* Display results on a map

v1.2.1 (released 2016-03-21)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.2.0...v1.2.1

* Fix EMAIL_HANDLER
* Add `django` logger
* Prevent Celery from hijacking the root logger

v1.2.0 (released 2016-03-14)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.1.1...v1.2.0

* Settings changes:
    - Update `LOGGING` to reflect sending logs to `syslog`
    - Utility for grabbing settings from the environment
    - Utility for falling back to Django default settings
    - Email configuration
    - Remove unused `HOSTNAME` setting
    - Misc. settings tweaks related to deployment.

v1.1.1 (released 2016-03-01)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.1.0...v1.1.1

* Updated to Django==1.8.10 from Django==1.8.6
* Send Celery task error emails.
* Limit InboxMessages fetch to the past 7 days.
* Use relativedelta where possible.
* Update 404 page template.


v1.1.0 (released 2016-02-24)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.0.4...v1.1.0

Many changes, including:

* Break out deployment-related assets into a private repo.
* Update Celery task structure.
    - **Note:** Existing tasks are probably very backed up. After deploy,
      purge all existing tasks (see
      `Celery FAQ <http://docs.celeryproject.org/en/latest/faq.html#how-do-i-purge-all-waiting-tasks>`_).
* Chart enhancements on Poll detail and PollRun detail pages.
* Filters on Recent Indicators, Poll detail, and PollRun detail pages.


v1.0.4 (never released)
-----------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.0.3...v1.0.4

* Update versions of Celery-related packages.


v1.0.3 (released 2015-11-30)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.0.2...v1.0.3

* Bug fix for clearing spoof data. See `#100 <https://github.com/rapidpro/tracpro/pull/100>`_.
* Release notes added for ReadTheDocs builds


v1.0.2 (released 2015-11-25)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.0.1...v1.0.2

* Don't paginate results on responses CSV export.
* Show participant count in participant column on PollRun ByPoll page.

v1.0.1 (released 2015-11-25)
-----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v1.0.0...v1.0.1

* Updated contact sync to run every 30 minutes, rather than every 5.

v1.0.0 (released 2015-11-19)
----------------------------

Code diff: https://github.com/rapidpro/tracpro/compare/v0.0.51...v1.0.0

* Add documentation to `ReadTheDocs <https://tracpro.readthedocs.org>`_.
* Upgrade version requirements.

  - **Note:** Due to a change in structure for `django-celery`, you will
    need to run `python manage.py migrate djcelery --fake-initial` before
    running new migrations.
* Add `prod_db_to_staging` Fabric command.
* Fix `hostname` in `manage_run` Fabric command so that it now runs without
  error.
* Require that source is updated before updating pip requirements during
  deploy.

  - **Note:** Pip requirements were sometimes being updated before the
    source code was updated. If you have this issue before updating to
    v1.0.0, run the deploy again to solve.
* Add deadsnakes Python 2.7 to deploy environment.

  - **Note:** An SSL dependency requires Python 2.7.9 or greater. If your
    deployment is using a lower version, destroy the virtual environment
    before your next deploy so that it is rebuilt.
* Add org config option to show/hide spoof data. See
  `#92 <https://github.com/rapidpro/tracpro/pull/92>`_.

  - **Note:** A migration sets the default to False for all orgs except
    "Caktus".
* Fix unicode bug when setting a Contact DataField value. See
  `#88 <https://github.com/rapidpro/tracpro/pull/88>`_.
* Use ``django.utils.dateparser`` rather than ``dateutil`` when parsing
  datetimes for DataFields. See `#88 <https://github.com/rapidpro/tracpro/pull/88>`_.
* Fix org languages bugs. See `#91 <https://github.com/rapidpro/tracpro/pull/91>`_.


.. _semantic versioning: http://semver.org/
