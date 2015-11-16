Deployment Process
==================

Release to staging
------------------

See the :doc:`Fabric commands documentation</servers/fabric>` for information on how to
reset the staging data from production and how to run commands on the servers.

#. Ensure that your work has been pushed to GitHub.

#. On your local machine, check out the branch that you wish to deploy.

#. By default, the ``develop`` branch is deployed to staging (regardless of
   which branch you've checked out locally). If you wish to
   deploy a different branch, you will need to edit your local copy of
   `conf/pillar/staging.sls <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_ to use
   a different branch name.

#. Run the deploy::

    fab staging deploy

Release to production
---------------------

#. **Before** merging the changes to ``master``, the complete deployment
   process should be tested on staging.:

   * Copy the production database and media files to staging::

        fab prod_to_staging

   * On your local machine, check out the master branch::

        git checkout master

   * Edit your local copy of `conf/pillar/staging.sls <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_ to specify the ``master`` branch for deployment.

   * Deploy the current ``master`` branch to staging::

       fab staging deploy

   * Undo the change to `conf/pillar/staging.sls <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_.

#. Now that the staging environment matches production, check out and deploy the new ``develop`` branch
   to staging::

     git checkout develop
     fab staging deploy

   **NOTE:** If you are deploying a hotfix branch, you will need to edit
   your local copy of `conf/pillar/staging.sls <https://github.com/rapidpro/tracpro/blob/develop/conf/pillar/staging.sls>`_ accordingly.

#. Confirm that changes are behaving as expected, and troubleshoot the
   deploy process until you are confident.

#. Merge all changes to the ``master`` branch, ensure that these changes
   are pushed to GitHub, and confirm that the Travis build has passed.

#. Check out the updated ``master`` branch locally, and create a release tag::

    git tag -a YYYY-MM-DD -m "Released YYYY-MM-DD" && git push origin --tags

   If you make more than one release on a particular day, append a release
   count to the tag name - for example, ``YYYY-MM-DD``, ``YYYY-MM-DD.1``,
   ``YYYY-MM-DD.2``, etc.

#. Add release notes via the GitHub releases interface.

#. Run the production deploy::

    fab production deploy

#. Merge the ``master`` branch into ``develop``::

    git checkout develop
    git merge origin/master
    git push origin develop