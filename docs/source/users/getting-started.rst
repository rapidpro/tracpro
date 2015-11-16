Getting Started
======================

The following steps take you through the process of creating a new organization in TracPro. If you are using your local development installation, then ensure that both the web server and Celery are running.

Preparing RapidPro
-----------------------

Before setting up your TracPro organization, one should ensure that the RapidPro organization has the following:

* A set of contact groups representing geographical regions, e.g. *Kigali*, *Florida*
* A set of contact groups representing reporting groups, e.g. *Males*, *Teachers*

Obviously you will also want to define some flows in RapidPro which are suitable for running as polls.

Creating An Organization In TracPro
------------------------------------

 * Navigate to http://localhost:8000/
 * Log in as a superuser
 * Navigate to http://localhost/manage/user/ and add a new administrator user account
 * Navigate to http://localhost/manage/org/ and click *Add* to create a new organization
 * Include the newly created user as an administrator
 * Use the API token provided by your RapidPro organization. If you don't know it then visit the `API explorer <https://app.rapidpro.io/api/v1/explorer>`_.
 * Save new org and navigate to http://SUBDOMAIN.localhost:8000/ where SUBDOMAIN is the subdomain of your new organization
 * Log in as the new administrator user

Configuring An Organization
----------------------------

There won't be much to see until you tell TracPro about which flows and groups to use.

 * Navigate to **Administration** > **Polls** and click **Select** to select which flows in RapidPro will be used as polls in TracPro
 * Navigate to **Administration** > **Reporter Groups** and click **Select** to select which contact groups in RapidPro will be used as reporter groups in TracPro
 * Navigate to **Administration** > **Regions** and click **Select** to select which contact groups in RapidPro will be used as regions in TracPro. This will trigger a fetch of all contacts from those groups.

Management Tasks
------------------

Fetching old runs
------------------

If a new poll is added, TracPro will only track runs made after the poll has been added. If you need to fetch older runs, then there is a management task which allows you to do this. The command takes two parameters:

#. The database id of the organization
#. A number of minutes, hours or days::

    # fetches all runs for org #1 made in the last 45 minutes
    $ ./manage.py fetchruns 1 --minutes=45

    # fetches all runs for org #2 made in the last 6 hours
    $ ./manage.py fetchruns 2 --hours=6

    # fetches all runs for org #3 made in the last 2 days (48 hours)
    $ ./manage.py fetchruns 3 --days=2


**One should use this command with caution as it could potentially try to download a very high number of runs**