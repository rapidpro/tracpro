Changelog
=========

Tracpro's version is incremented upon each merge to master according to our
:ref:`production deployment process <release-to-production>`.

We recommend reviewing the release notes and code diffs before upgrading
between versions.

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
