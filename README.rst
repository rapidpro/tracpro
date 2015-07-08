Tracpro
=======

Below you will find basic setup and deployment instructions for the tracpro
project. To begin you should have the following applications installed on your
local development system::

- Python 2.7
- `pip <http://www.pip-installer.org/>`_ >= 1.5
- `virtualenv <http://www.virtualenv.org/>`_ >= 1.10
- `virtualenvwrapper <http://pypi.python.org/pypi/virtualenvwrapper>`_ >= 3.0
- Postgres >= 9.3
- git >= 1.7

Getting Started
---------------

First clone the repository from Github and switch to the new directory::

    $ git clone git@github.com:[ORGANIZATION]/tracpro.git
    $ cd tracpro

To setup your local environment you should create a virtualenv and install the
necessary requirements::

    # Check that you have python3.4 installed
    $ which python3.4
    $ mkvirtualenv tracpro -p `which python3.4`
    (tracpro)$ $VIRTUAL_ENV/bin/pip install -r $PWD/requirements/dev.txt

Then create a local settings file and set your ``DJANGO_SETTINGS_MODULE`` to use it::

    (tracpro)$ cp tracpro/settings/local.example.py tracpro/settings/local.py
    (tracpro)$ echo "export DJANGO_SETTINGS_MODULE=tracpro.settings.local" >> $VIRTUAL_ENV/bin/postactivate
    (tracpro)$ echo "unset DJANGO_SETTINGS_MODULE" >> $VIRTUAL_ENV/bin/postdeactivate

Exit the virtualenv and reactivate it to activate the settings just changed::

    (tracpro)$ deactivate
    $ workon tracpro

Create the Postgres database and run the initial migrate::

    (tracpro)$ createdb -E UTF-8 tracpro
    (tracpro)$ python manage.py migrate

You should now be able to run the development server::

    (tracpro)$ python manage.py runserver


Deployment
----------

The deployment of requires Fabric but Fabric does not yet support Python 3. You
must either create a new virtualenv for the deployment::

    # Create a new virtualenv for the deployment
    $ mkvirtualenv tracpro-deploy -p `which python2.7`
    (tracpro-deploy)$ pip install -r requirements/deploy.txt

or install the deploy requirements
globally.::

    $ sudo pip install -r requirements/deploy.txt


You can deploy changes to a particular environment with
the ``deploy`` command::

    $ fab staging deploy

New requirements or South migrations are detected by parsing the VCS changes and
will be installed/run automatically.
