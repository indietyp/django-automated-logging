""" Test everything related to requests """
import json
from copy import deepcopy

from django.http import JsonResponse

from automated_logging.models import RequestEvent
from automated_logging.tests.base import BaseTestCase, USER_CREDENTIALS
from automated_logging.tests.helpers import random_string


class SimpleLoggedOutRequestsTestCase(BaseTestCase):
    def setUp(self):
        from django.conf import settings
        from automated_logging.settings import settings as conf

        self.backup = deepcopy(
            settings.AUTOMATED_LOGGING['request']['exclude']['applications']
        )

        settings.AUTOMATED_LOGGING['request']['exclude']['applications'] = []
        conf.load.cache_clear()

        super().setUp()

        RequestEvent.objects.all().delete()

    def tearDown(self) -> None:
        from django.conf import settings

        super().tearDown()

        settings.AUTOMATED_LOGGING['request']['exclude']['applications'] = self.backup

    @staticmethod
    def view(request):
        return JsonResponse({})

    def test_simple(self):
        RequestEvent.objects.all().delete()

        self.request('GET', self.view)

        events = RequestEvent.objects.all()
        self.assertEqual(events.count(), 1)

        event = events[0]

        self.assertEqual(event.user, None)


class SimpleLoggedInRequestsTestCase(BaseTestCase):
    def setUp(self):
        from django.conf import settings
        from automated_logging.settings import settings as conf

        self.backup = deepcopy(
            settings.AUTOMATED_LOGGING['request']['exclude']['applications']
        )

        settings.AUTOMATED_LOGGING['request']['exclude']['applications'] = []
        conf.load.cache_clear()

        super().setUp()

        self.client.login(**USER_CREDENTIALS)

        RequestEvent.objects.all().delete()

    def tearDown(self) -> None:
        from django.conf import settings

        super().tearDown()

        settings.AUTOMATED_LOGGING['request']['exclude']['applications'] = self.backup

    @staticmethod
    def view(request):
        return JsonResponse({})

    def test_simple(self):
        RequestEvent.objects.all().delete()

        self.request('GET', self.view)

        events = RequestEvent.objects.all()
        self.assertEqual(events.count(), 1)

        event = events[0]

        self.assertEqual(event.ip, '127.0.0.1')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.status, 200)
        self.assertEqual(event.method, 'GET')
        self.assertEqual(event.uri, '/')

    def test_404(self):
        RequestEvent.objects.all().delete()

        self.client.get(f'/{random_string()}')

        events = RequestEvent.objects.all()
        self.assertEqual(events.count(), 1)

        event = events[0]
        self.assertEqual(event.status, 404)

    @staticmethod
    def exception(request):
        raise Exception

    def test_500(self):
        RequestEvent.objects.all().delete()

        try:
            self.request('GET', self.exception)
        except:
            pass

        events = RequestEvent.objects.all()
        self.assertEqual(events.count(), 1)

        event = events[0]
        self.assertGreaterEqual(event.status, 500)


class SimpleDataRecordingRequestsTestCase(BaseTestCase):
    def setUp(self):
        from django.conf import settings
        from automated_logging.settings import settings as conf

        self.backup = deepcopy(settings.AUTOMATED_LOGGING['request'])

        settings.AUTOMATED_LOGGING['request']['exclude']['applications'] = []
        settings.AUTOMATED_LOGGING['request']['data']['enabled'] = [
            'response',
            'request',
        ]
        conf.load.cache_clear()

        super().setUp()

        self.client.login(**USER_CREDENTIALS)

        RequestEvent.objects.all().delete()

    def tearDown(self) -> None:
        from django.conf import settings

        super().tearDown()

        settings.AUTOMATED_LOGGING['request'] = self.backup

    @staticmethod
    def view(request):
        return JsonResponse({'test': 'example'})

    def test_payload(self):
        # TODO: preliminary until request/response parsing is implemented
        RequestEvent.objects.all().delete()

        self.request('GET', self.view, data=json.dumps({'X': 'Y'}))

        events = RequestEvent.objects.all()
        self.assertEqual(events.count(), 1)

        response = json.dumps({'test': 'example'})
        request = json.dumps({'X': 'Y'})
        event = events[0]
        self.assertEqual(event.response.content.decode(), response)
        self.assertEqual(event.request.content.decode(), request)