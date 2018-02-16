from django.apps import AppConfig


class AutomatedloggingConfig(AppConfig):
    name = 'automated_logging'
    verbose_name = 'Django Automated Logging (DJL)'

    def ready(self):
      from .signals import request, database, m2m
      from .handlers import DatabaseHandler
