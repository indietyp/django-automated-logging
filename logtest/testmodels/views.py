from django.http import JsonResponse
from django.shortcuts import render

from testmodels.models import OrdinaryTest


def save_test(request):
    """just for testing the save capabilities internally"""

    print('hello there young man')
    ordinary = OrdinaryTest.objects.filter()[0]
    ordinary.test = 'abc'
    ordinary.save()
    return JsonResponse({})
