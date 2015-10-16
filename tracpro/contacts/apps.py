from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = "tracpro.contacts"

    def ready(self):
        from . import signals  # noqa
