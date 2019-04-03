import logging
import string
import time

from .models import *
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from testmodels.models import Base, ForeignTest, M2MTest, OneToOneTest, OrdinaryTest

"""
TODO:
  - atomic test for model changes
"""


class RequestTestCase(TestCase):
  def setUp(self):
    self.c = Client()

    self.user = User.objects.create_user(username='example', password='example')
    self.user.save()

  def test_request_based_database_logging_logged_in(self):
    self.c.login(username='example', password='example')

    response = self.c.get('')
    assert response.status_code == 200
    assert Request.objects.all().count() == 1

    entry = Request.objects.all()[0]
    assert entry.uri == '/'
    assert entry.method == 'GET'
    assert entry.user == self.user

    self.c.logout()

  def test_request_based_database_logging_logged_out(self):
    response = self.c.post('')
    assert response.status_code == 200
    assert Request.objects.all().count() == 1

    entry = Request.objects.all().order_by('-created_at')[0]
    assert entry.uri == '/'
    assert entry.method == 'POST'
    assert entry.user is None

  def test_request_based_database_logging_exception(self):
    try:
      # this is designed to fail!
      self.c.get('/500')
    except Exception:
      pass

    assert Request.objects.all().count() == 1

    entry = Request.objects.all().order_by('-created_at')[0]
    assert entry.uri == '/500'
    assert entry.status == 500

  def test_request_based_database_logging_not_found(self):
    try:
      # this is designed to fail!
      self.c.get('/404')
    except Exception:
        pass

    assert Request.objects.all().count() == 1

    entry = Request.objects.all().order_by('-created_at')[0]
    assert entry.uri == '/404'
    assert entry.status == 404

  def test_request_based_database_maxage(self):
    config = settings.LOGGING
    config['handlers']['db']['maxage'] = 'PT2S'
    logging.config.dictConfig(config)

    response = self.c.post('')
    time.sleep(2)

    assert response.status_code == 200
    assert Request.objects.all().count() == 1

    response = self.c.post('')
    time.sleep(.5)

    assert response.status_code == 200
    assert Request.objects.all().count() == 1

    config['handlers']['db']['maxage'] = None
    logging.config.dictConfig(config)


class ModeltestCase(TestCase):
  def setUp(self):
    self.c = Client()

    self.user = User.objects.create_user(username='example', password='example')
    self.user.save()

    self.c.login(username='example', password='example')

    self._baseset = [Base() for _ in range(10)]
    [x.save() for x in self._baseset]

    # clean up before every test
    Model.objects.all().delete()

  def test_model_based_database_m2m(self):
    m2m = M2MTest()
    m2m.save()

    assert Model.objects.count() == 1

    m2m = M2MTest.objects.all()[0]
    m2m.test.set(self._baseset[:-1])
    m2m.save()

    assert Model.objects.count() == 2
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.modification.inserted.count() == 9
    assert entry.modification.inserted.all()[0].type.app_label == 'testmodels'
    assert entry.modification.inserted.all()[0].type.model == 'base'

    m2m = M2MTest.objects.all()[0]
    m2m.test.add(self._baseset[-1])
    m2m.save()

    assert Model.objects.count() == 3
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.modification.inserted.count() == 1

    m2m = M2MTest.objects.all()[0]
    m2m.test.remove(self._baseset[-1])
    m2m.save()

    assert Model.objects.count() == 4
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.modification.removed.count() == 1

  def test_model_based_database_foreign(self):
    foreign = ForeignTest()
    foreign.save()

    assert Model.objects.count() == 1

    foreign = ForeignTest.objects.all()[0]
    foreign.test = self._baseset[2]
    foreign.save()

    assert Model.objects.count() == 2
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.action == 2

    affected = entry.modification.modification.currently.all()[0]
    assert affected.field.name == 'test_id'
    assert affected.value == str(self._baseset[2].id)

  def test_model_based_database_onetoone(self):
    one = OneToOneTest()
    one.save()

    assert Model.objects.count() == 1

    one = OneToOneTest.objects.all()[0]
    one.test = self._baseset[1]
    one.save()

    assert Model.objects.count() == 2
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.action == 2

    affected = entry.modification.modification.currently.all()[0]
    assert affected.field.name == 'test_id'
    assert affected.value == str(self._baseset[1].id)

  def test_model_based_database_ordinary(self):
    ordinary = OrdinaryTest()
    ordinary.save()

    assert Model.objects.count() == 1
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.action == 1

    ordinary = OrdinaryTest.objects.all()[0]
    ordinary.test = string.ascii_lowercase
    ordinary.save()

    assert Model.objects.count() == 2
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.action == 2

    affected = entry.modification.modification.currently.all()[0]
    assert affected.field.name == 'test'
    assert affected.value == string.ascii_lowercase

    ordinary = OrdinaryTest.objects.all()[0]
    ordinary.delete()

    assert Model.objects.count() == 3
    entry = Model.objects.all().order_by('-created_at')[0]

    assert entry.action == 3


class HandlerTestCase(TestCase):
  def setUp(self):
    self.logger = logging.getLogger(__name__)

  def test_handler_unspecified_catch(self):
    self.logger.error('TEST')

    assert Unspecified.objects.all().count() == 1
    assert Unspecified.objects.all()[0].message == 'TEST'
