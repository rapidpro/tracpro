#TracPro

Dashboard for managing polls hosted in [RapidPro](http://rapidpro.io)

Built for UNICEF by [Nyaruka](http://nyaruka.com)

##System Requirements

 * [PostgreSQL](http://www.postgresql.org/)
 * [Redis](http://redis.io/)
 * [Python 2.7](https://www.python.org/)

##Development Setup

Clone the project source code:

```
% git clone https://github.com/rapidpro/tracpro.git
```

Install Python dependencies:

```
% cd tracpro
% virtualenv env
% source env/bin/activate
% pip install -r pip-requires.txt
```

Create the PostgreSQL database (enter password _nyaruka_ when prompted):

```
% createdb tracpro
% createuser tracpro -P -E
% psql -c "GRANT ALL PRIVILEGES ON DATABASE tracpro to tracpro;"
```

Link up the development settings file

```
% ln -s tracpro/settings.py.postgres tracpro/settings.py
```

Sync the database, add all our models and create our superuser

```
% python manage.py syncdb
% python manage.py createsuperuser
```

At this point everything should be good to go, you can start with:

```
% python manage.py runserver
```

To run background tasks, you'll also need to start celery:

```
% celery -A tracpro worker -B -l info
```

###Running Tests

```
% coverage run --source="." manage.py test --verbosity=2 --noinput
% coverage report -m --include="tracpro/*" --omit="*/migrations/*,*/tests.py"
```

###Subdomain Setup

TracPro uses subdomains to determine which organization a user is currently accessing. For example, if you create an organization with the subdomain _testing_, you should configure that as an alias for localhost. On a UNIX-like system you would edit /etc/hosts as follows:

```
127.0.0.1	localhost testing.localhost
```

### RapidPro Integration

The default development settings file connects to [rapidpro.io](http://rapidpro.io). To integrate with a different 
RapidPro instance, either edit this file or create a new settings file.

## Getting Started

The following steps take you through the process of creatin. If you are using your local development installation, then ensure that both the webserver and celery are running.
 
### Creating An Organization

 * Navigate to http://localhost:8000/
 * Login as the superuser
 * Navigate to http://localhost/manage/user/ and add a new administrator user account
 * Navigate to http://localhost/manage/org/ and click _Add_ to create a new organization
 * Include the newly created user as an administrator
 * Use the API token provided by your RapidPro organization. If you don't know it then visit the [API explorer](https://rapidpro.io/api/v1/explorer).
 * Save new org and navigate to http://SUBDOMAIN.localhost:8000/ where SUBDOMAIN is the subdomain of your new organization
 * Login in as the new administrator user

### Configuring An Organization

There won't be much to see until you tell TracPro about which flows and groups to use.

 * Navigate to _Administration_ &rarr; _Polls_ and click _Select_ to select which flows in RapidPro will be used as polls in TracPro
 * Navigate to _Administration_ &rarr; _Reporter Groups_ and click _Select_ to select which contact groups in RapidPro will be used as reporter groups in TracPro
 * Navigate to _Administration_ &rarr; _Regions_ and click _Select_ to select which contact groups in RapidPro will be used as regions in TracPro. This will trigger a fetch of all contacts from those groups.
