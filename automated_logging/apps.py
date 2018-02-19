from django.apps import AppConfig
from .settings import AUTOMATED_LOGGING


class AutomatedloggingConfig(AppConfig):
    name = 'automated_logging'
    verbose_name = 'Django Automated Logging (DAL)'

    def ready(self):
      if 'request' in AUTOMATED_LOGGING['modules']:
        from .signals import request
      if 'model' in AUTOMATED_LOGGING['modules']:
        from .signals import database, m2m

      from .handlers import DatabaseHandler
