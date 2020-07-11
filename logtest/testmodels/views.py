from django.http import JsonResponse
from django.shortcuts import render

from automated_logging.decorators import ignore_view, include_view
from testmodels.models import OrdinaryTest, M2MTest, Base, OneToOneTest
import random
import logging

logger = logging.getLogger(__name__)


def save_test(request):
    """just for testing the save capabilities internally"""

    # print('hello there young man')
    base = Base.objects.get(pk='2fd93db1-bcba-4282-b97f-4fd88f8a3cd8')
    # print(base.id)

    m2m = M2MTest.objects.get(pk='16b18608-11dd-47f7-a7d6-c1bb427110ac')
    # m2m.test.remove(base)
    # m2m.test.clear()
    # m2m.test.add(base)
    # m2m.save()
    # base.m2mtest_set.set([])
    # base.save()

    # o2o = OneToOneTest()
    # o2o.test = base
    # o2o.save()
    ordinary = OrdinaryTest.objects.filter()[0]
    ordinary.test = str(random.randint(0, 10000000))
    ordinary.save(update_fields=['test'])

    logger.warning('hello there')

    return JsonResponse({})


@ignore_view(methods=['POST'])
def decorator_test(request):
    return JsonResponse({})
