from django.apps import AppConfig
from .settings import settings


class AutomatedloggingConfig(AppConfig):
    name = 'automated_logging'
    verbose_name = 'Django Automated Logging (DAL)'

    def ready(self):
        if 'request' in settings.modules:
            from .signals import request
        # if 'model' in settings.modules:
        #     from .signals import database, m2m
        #
        # from .handlers import DatabaseHandler
