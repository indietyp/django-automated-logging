"""
Handles the request portion of the handlers.

This files handles processig all the request related signals.
These signals are all django interal ones.
"""
import logging
from logging import CRITICAL, WARNING

from .. import settings
from django.dispatch import receiver
from django.core.handlers.wsgi import WSGIRequest
from django.core.signals import request_finished, got_request_exception
from . import get_current_environ, get_current_user


@receiver(request_finished, weak=False)
def request_finished_callback(sender, **kwargs):
    """This function logs if the user acceses the page"""
    logger = logging.getLogger(__name__)
    level = settings.AUTOMATED_LOGGING['loglevel']['request']

    user = get_current_user()
    uri, application, method, status = get_current_environ()

    excludes = settings.AUTOMATED_LOGGING['exclude']['request']
    if status in excludes:
        return

    if method.lower() in excludes:
        return

    logger.log(level, ('%s performed request at %s (%s %s)' % (user, uri, method, status)).replace("  ", " "), extra={
        'action': 'request',
        'data': {
            'user': user,
            'uri': uri,
            'method': method,
            'application': application,
            'status': status
        }
    })


@receiver(got_request_exception, weak=False)
def request_exception(sender, request, **kwargs):
    """
    Automated request exception logging.

    The function can also return an WSGIRequest exception,
    which does not supply either status_code or reason_phrase.
    """
    if not isinstance(request, WSGIRequest):
        logger = logging.getLogger(__name__)
        level = CRITICAL if request.status_code <= 500 else WARNING

        logger.log(level, '%s exception occured (%s)', request.status_code, request.reason_phrase)

    else:
        logger = logging.getLogger(__name__)
        logger.log(WARNING, 'WSGIResponse exception occured')
