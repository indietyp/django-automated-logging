""" Test base every unit test uses """
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase, Client

User: AbstractUser = get_user_model()
USER_CREDENTIALS = {'username': 'example', 'password': 'example'}


class BaseTestCase(TestCase):
    def __init__(self, methodName):
        from django.conf import settings

        settings.AUTOMATED_LOGGING_DEV = True

        super().__init__(methodName)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(**USER_CREDENTIALS)
        self.user.save()
