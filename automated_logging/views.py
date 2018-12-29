from django.http import JsonResponse


def request_testcase(request):
  return JsonResponse({})


def exception_testcase(request):
  raise Exception
