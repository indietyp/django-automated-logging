import threading
import django

if django.VERSION[0] == 1 and django.VERSION[1] < 10:
  from django.core.urlresolvers import resolve
else:
  from django.urls import resolve


class AutomatedLoggingMiddleware:
  thread_local = threading.local()

  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    request_uri = request.get_full_path()
    AutomatedLoggingMiddleware.thread_local.current_user = request.user
    AutomatedLoggingMiddleware.thread_local.method = request.method
    AutomatedLoggingMiddleware.thread_local.request_uri = request_uri
    AutomatedLoggingMiddleware.thread_local.application = resolve(request.path).func.__module__.split('.')[0]

    response = self.get_response(request)
    return response
