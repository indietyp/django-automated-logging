""" Test base every unit test uses """
import importlib
from copy import deepcopy, copy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase, RequestFactory
from django.urls import path

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
        self.request_factory = RequestFactory()

        self.user = User.objects.create_user(**USER_CREDENTIALS)
        self.user.save()
