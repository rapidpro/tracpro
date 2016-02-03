import os

from . import load_env


load_env.load_env()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracpro.settings")

from django.core.wsgi import get_wsgi_application  # noqa

application = get_wsgi_application()
