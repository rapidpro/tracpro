Fabric commands
===============

TracPro uses the `Caktus project template
<https://github.com/caktus/django-project-template>`_. See the :doc:`server documentation</servers/server-setup>` to learn more about server architecture and
provisioning.

Before using fabric commands, follow all of the steps in the
:doc:`developer setup docs </developers/local-developer-setup>` to ensure that you have all of the
required credentials.

You can get a full list of Fabric commands by running ``fab --list``, or read
through the source at `fabfile.py <https://github.com/rapidpro/tracpro/blob/develop/fabfile.py>`_.

Copying data for local development
----------------------------------

To copy the database and media files from a remote server to your local
development environment::

    fab [production|staging] mirror_to_dev

**NOTE:** Migrations must be run (``django-admin migrate``) if the local
branch has migrations that have not yet been run on the remote server.

Copying production data to staging
----------------------------------

To copy the production database and media files to staging::

    fab prod_to_staging

**NOTES:** Media files will be synced through the local development
environment first. Additionally, migrations must run
(``fab staging manage_run:"migrate"``) if the branch that is deployed on
staging has new migrations that have not been run on production.

Running commands on the server
------------------------------

To run a management command on a remote server::

    fab [production|staging] manage_run:"command_name -arg --option param1 param2"

Use the ``manage_shell`` alias to run a Python shell on a remote server::

    fab [production|staging] manage_shell