import logging
from django.test import TestCase
from django.test import Client
from django.db import transaction
from django.contrib.auth.models import User
from .models import *
from testmodels.models import Base, M2MTest, ForeignTest, OneToOneTest, OrdinaryTest
import string


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
    assert entry.user == self.user

    self.c.logout()

  def test_request_based_database_logging_logged_out(self):
    response = self.c.get('')
    assert response.status_code == 200
    assert Request.objects.all().count() == 1

    entry = Request.objects.all().order_by('-created_at')[0]
    assert entry.uri == '/'
    assert entry.user is None


# add database test, thx
# add transation atomic test
class ModeltestCase(TestCase):
  def setUp(self):
    self.c = Client()

    self.user = User.objects.create_user(username='example', password='example')
    self.user.save()

    self.c.login(username='example', password='example')

    self.baseset = [Base() for _ in range(10)]
    [x.save() for x in self.baseset]

  def test_model_based_database_m2m(self):
    m2m = M2MTest()
    m2m.save()

    m2m.test.set(self.baseset[:-1])
    m2m.save()

    m2m.test.add(self.baseset[-1])
    m2m.save()

    m2m.test.remove(self.baseset[-1])
    m2m.save()

  def test_model_based_database_foreign(self):
    foreign = ForeignTest()
    foreign.save()

    foreign.test = self.baseset[2]
    foreign.save()

  def test_model_based_database_onetoone(self):
    one = OneToOneTest()
    one.save()

    one.test = self.baseset[1]
    one.save()

  def test_model_based_database_ordinary(self):
    ordinary = OrdinaryTest()
    ordinary.save()

    ordinary.test = string.ascii_lowercase
    ordinary.save()

    ordinary.delete()


class HandlerTestCase(TestCase):
  def setUp(self):
    self.logger = logging.getLogger(__name__)

  def test_handler_unspecified_catch(self):
    self.logger.error('TEST')
    assert Unspecified.objects.all().count() == 1
    assert Unspecified.objects.all()[0].message == 'TEST'
