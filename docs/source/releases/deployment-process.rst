Deployment Process
==================

Release to staging
------------------

#. Ensure that your work has been pushed to GitHub.

#. On your local machine, check out the branch that you wish to deploy.

#. By default, the ``develop`` branch is deployed to staging (regardless of
   which branch you've checked out locally). If you wish to
   deploy a different branch, you will need to edit your local copy of
   `conf/pillar/staging.sls
   <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_
   to use a different branch name.

#. Run the deploy::

    fab staging deploy


.. _reset-staging-environment:

Reset staging environment
-------------------------

These steps will restore the production database and code states to the
staging environment.

#. Copy the production database to staging::

    fab prod_db_to_staging

#. On your local machine, check out the master branch::

    git checkout master

#. Edit your local copy of `conf/pillar/staging.sls
   <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_
   to specify the ``master`` branch for deployment.

#. Deploy the ``master`` branch to staging::

    fab staging deploy

#. Undo the change to `conf/pillar/staging.sls
   <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_.


.. _release-to-production:

Release to production
---------------------

#. **Before** merging changes to ``master``, the complete deployment process
   should be tested on staging.

   * :ref:`Restore <reset-staging-environment>` production data, media, and code
     to the staging machine.

   * Check out the ``develop`` branch locally and deploy it to staging::

       fab staging deploy

     **NOTE:** If you are deploying a hotfix branch, you will need to edit
     your local copy of `conf/pillar/staging.sls
     <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_
     accordingly.

   * Confirm that changes are behaving as expected, and troubleshoot the
     deploy process until you are confident.

#. Finalize the release number.

   * Update the version number according to `semantic versioning`_, and change
     the version state to ``"final"``. Version must be updated in
     ``tracpro/__init__.py`` and ``docs/source/conf.py``.

       * The micro version is incremented with backwards-compatible bugfixes.

       * The minor version is incremented with backwards-compatible features.

       * The major version is incremented with incompatible changes.

   * Update the :doc:`release notes <changelog>` (including notes about
     one-off deployment requirements, if needed) and add the current date as
     the release date.

   * Commit these changes and push to GitHub.

#. Merge all changes to the ``master`` branch, ensure that these changes
   are pushed to GitHub, and confirm that the Travis build has passed.

#. Check out the updated ``master`` branch locally, and create a release tag::

    git tag -a vX.Y.Z -m "Released YYYY-MM-DD" && git push origin --tags

#. Copy the release notes to the GitHub releases interface.

#. Run the production deploy::

    fab production deploy

#. Merge the ``master`` branch into ``develop``::

    git checkout develop
    git merge origin/master
    git push origin develop

#. On the ``develop`` branch, increment the micro version and change the code
   state to ``"dev"``. Commit these changes and push to GitHub.

#. Run ReadTheDocs builds for the new release & the latest develop.


.. _semantic versioning: http://semver.org/
