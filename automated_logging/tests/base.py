""" Test base every unit test uses """
import importlib
from copy import copy, deepcopy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase, RequestFactory
from django.urls import path

from automated_logging.helpers import namedtuple2dict
from automated_logging.middleware import AutomatedLoggingMiddleware
from automated_logging.models import ModelEvent, RequestEvent, UnspecifiedEvent
from automated_logging.signals import cached_model_exclusion

User: AbstractUser = get_user_model()
USER_CREDENTIALS = {'username': 'example', 'password': 'example'}


class BaseTestCase(TestCase):
    def __init__(self, method_name):
        from django.conf import settings

        settings.AUTOMATED_LOGGING_DEV = True

        super().__init__(method_name)

    def request(self, method, view, data=None):
        """
        request a specific view and return the response.

        This is not ideal and super hacky. Backups the actual urlpatterns,
        and then overrides the urlpatterns with a temporary one and then
        inserts the new one again.
        """

        urlconf = importlib.import_module(settings.ROOT_URLCONF)

        backup = copy(urlconf.urlpatterns)
        urlconf.urlpatterns.clear()
        urlconf.urlpatterns.append(path('', view))

        response = self.client.generic(method, '/', data=data)

        urlconf.urlpatterns.clear()
        urlconf.urlpatterns.extend(backup)

        return response

    def setUp(self):
        from django.conf import settings
        from automated_logging.settings import default, settings as conf

        self.user = User.objects.create_user(**USER_CREDENTIALS)
        self.user.save()

        self.original_config = deepcopy(settings.AUTOMATED_LOGGING)

        base = namedtuple2dict(default)

        settings.AUTOMATED_LOGGING.clear()
        for key, value in base.items():
            settings.AUTOMATED_LOGGING[key] = deepcopy(value)

        conf.load.cache_clear()
        super().setUp()
        # reset automated_logging configuration via default and then reset when done

    def tearDown(self) -> None:
        from django.conf import settings
        from automated_logging.settings import settings as conf

        super().tearDown()

        settings.AUTOMATED_LOGGING.clear()
        for key, value in self.original_config.items():
            settings.AUTOMATED_LOGGING[key] = deepcopy(value)

        conf.load.cache_clear()

        if hasattr(AutomatedLoggingMiddleware.thread, 'dal'):
            delattr(AutomatedLoggingMiddleware.thread, 'dal')

        cached_model_exclusion.cache_clear()

    @staticmethod
    def clear():
        """ clear all events """
        ModelEvent.objects.all().delete()
        RequestEvent.objects.all().delete()
        UnspecifiedEvent.objects.all().delete()

    def bypass_request_restrictions(self):
        from django.conf import settings
        from automated_logging.settings import settings as conf

        settings.AUTOMATED_LOGGING['request']['exclude']['status'] = []
        settings.AUTOMATED_LOGGING['request']['exclude']['methods'] = []
        conf.load.cache_clear()

        self.clear()
