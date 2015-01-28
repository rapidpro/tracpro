#TracPro

Dashboard for managing polls hosted in [RapidPro](http://rapidpro.io)

Built for UNICEF by [Nyaruka](http://nyaruka.com)

##Development Setup

Install dependencies

```
% virtualenv env
% source env/bin/activate
% pip install -r pip-requires.txt
```

Create the database

 * name: _tracpro_
 * username: _tracpro_
 * password: _nyaruka_

Link up a settings file

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

To run background tasks, you'll also need to start celery and have a local redis server:

```
% celery -A tracpro worker -B -l info
```

###Running Tests

```
% coverage run --source="." manage.py test --verbosity=2 --noinput
% coverage report -m --include="tracpro/*" --omit="*/migrations/*,*/tests.py"
```

##RapidPro Integration

TODO