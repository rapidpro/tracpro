Deployment Process
==================

Deployment and provisioning are currently managed in a separate repo.
Here we discuss the basic outline of our basic development and deployment practices.

Production deployment
---------------------

#. **Before merging changes to the master branch,** the deployment process
   must be tested from end to end on staging.

   * Restore current production data, media, and code (the current ``master``
     branch) to the staging machine.

   * Deploy the release branch to staging.

   * Confirm that changes are behaving as expected, and troubleshoot the
     deploy process until you are confident.

#. Update the :doc:`release notes <changelog>` (including notes about
   one-off deployment requirements, if needed) and add the current date as
   the release date. Commit these changes and push to GitHub.

#. Finalize the version number according to `semantic versioning`_, and change
   the version state to ``"final"``. Version must be updated in
   ``tracpro/__init__.py`` and ``docs/conf.py``.

     * The micro version is incremented with backwards-compatible bugfixes.

     * The minor version is incremented with backwards-compatible features.

     * The major version is incremented with incompatible changes.

   Commit these changes and push to GitHub.

#. Merge all changes to the ``master`` branch, ensure that these changes
   are pushed to GitHub, and confirm that the Travis build has passed.

#. Check out the updated ``master`` branch locally, and create a release tag::

    git tag -a vX.Y.Z -m "Released YYYY-MM-DD" && git push origin --tags

#. Copy the release notes to the GitHub releases interface.

#. Deploy the master branch to production.

#. Merge the ``master`` branch into ``develop``::

    git checkout develop
    git merge origin/master
    git push origin develop

#. On the ``develop`` branch, increment the micro version and change the code
   state to ``"dev"``. Commit these changes and push to GitHub.

#. `Run ReadTheDocs builds <https://readthedocs.org/projects/tracpro/>`_ for
   the new release & the latest develop.


.. _semantic versioning: http://semver.org/
