Local Development Environment Setup
====================================

Use this guide to bootstrap your local development environment.

**NOTE:** These instructions are written with Ubuntu in mind. Some adjustments
may be needed for Mac setup. To begin you should have the following applications installed on your local development system:

- Python 2.7
- `pip <http://www.pip-installer.org/>`_ >= 1.5
- `virtualenv <http://www.virtualenv.org/>`_ >= 1.10
- `virtualenvwrapper <http://pypi.python.org/pypi/virtualenvwrapper>`_ >= 3.0
- Postgres >= 9.3
- git >= 1.7

#. Install the LESS CSS precompiler and the CoffeeScript JavaScript compiler using ``npm``.
   First, install ``nodejs`` which comes with ``npm``::

    sudo apt-get install python-software-properties
    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install nodejs

   Then, use ``npm`` to install ``less`` and ``coffee``::

    sudo npm install less coffee-script -g

   **NOTE:** You may already have ``less``, ``coffee`` or ``npm`` installed.
   Before running installation commands, use ``which [program_name]`` to see
   if the path to the program's executable is known.

#. Clone the repo and check out the ``develop`` branch::

    $ git clone git@github.com:rapidpro/tracpro.git
    $ cd tracpro
    $ git checkout develop

#. Create a virtual environment using Python 2.7 and install the project
   requirements::

    # Check that you have python2.7 installed
    $ which python2.7
    $ mkvirtualenv tracpro -p `which python2.7`
    (tracpro)$ $VIRTUAL_ENV/bin/pip install -r $PWD/requirements/dev.txt

#. Create a local settings file::

    (tracpro)$ cp tracpro/settings/local.example.py tracpro/settings/local.py

   You may edit this file to make settings changes that are local to your
   machine. This file is listed in the `.gitignore
   <https://github.com/rapidpro/tracpro/blob/develop/.gitignore>`_ file and
   should never be checked into GitHub.

#. This project uses django-dotenv to manage environment variables. Configure
   the environment variable Django uses to locate the project settings file::

    (tracpro)$ echo "DJANGO_SETTINGS_MODULE=tracpro.settings.local" >> .env

#. Create a Postgres database and run the initial migrate::

    (tracpro)$ createdb -E UTF-8 tracpro
    (tracpro)$ python manage.py migrate

#. NOTE: TracPro uses `Smartmin <https://smartmin.readthedocs.org>`_ for permissions-based object scaffolding. If you make changes to a permission in GROUP_PERMISSIONS in `tracpro/settings/base.py <https://github.com/rapidpro/tracpro/blob/master/tracpro/settings/base.py>`_, you are required to migrate the database in order for that permission to take effect.

    (tracpro)$ python manage.py migrate

#. Background tasks. To run background tasks, you'll also need to start celery::

    (tracpro)$ celery -A tracpro worker -B -l info

#. Subdomain Setup

   TracPro uses subdomains to determine which organization a user is currently accessing. For example, if you create an organization with the subdomain **testing**, you should configure that as an alias for localhost. On a UNIX-like system you would edit /etc/hosts as follows::

    127.0.0.1   localhost. testing.localhost

#. RapidPro Integration

   The default development settings file connects to `app.rapidpro.io <http://app.rapidpro.io>`_.To integrate with a different RapidPro instance, either edit this file or create a new settings file.

#. Create Super User

   If creating a super user, be sure to select a valid password. TracPro enforces an 8 character minimum password.

#. Run the development server and navigate to
   `localhost:8000 <http://localhost:8000>`_::

    python manage.py runserver
