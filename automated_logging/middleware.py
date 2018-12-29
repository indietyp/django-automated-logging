import threading

from django.http import Http404
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin


class AutomatedLoggingMiddleware(MiddlewareMixin):
  """Get's access to the current things."""

  thread_local = threading.local()

  def process_request(self, request):
    request_uri = request.get_full_path()

    AutomatedLoggingMiddleware.thread_local.request = request
    AutomatedLoggingMiddleware.thread_local.current_user = request.user
    AutomatedLoggingMiddleware.thread_local.request_uri = request_uri

    try:
      AutomatedLoggingMiddleware.thread_local.application = resolve(request.path).func.__module__.split('.')[0]
    except Http404:
      AutomatedLoggingMiddleware.thread_local.application = ''

  def process_exception(self, request, exception):
    self.process_request(request)

  def process_response(self, request, response):
    AutomatedLoggingMiddleware.thread_local.method = request.method
    AutomatedLoggingMiddleware.thread_local.status = response.status_code
    return response
