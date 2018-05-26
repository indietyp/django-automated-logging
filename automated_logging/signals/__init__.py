"""
Helper functions for the files in this dir

A small clarification for the order of event triggering:

-> request_started
-> pre_save
-> (pre_delete)
-> post_save
-> (post_delete)
-> m2m_changed
-> request_finished
"""

import logging
from django.contrib.auth.models import AnonymousUser
from .. import settings
from ..middleware import AutomatedLoggingMiddleware
from ..models import Application


def validate_instance(instance):
    """Validating if the instance should be logged, or is excluded"""
    excludes = settings.AUTOMATED_LOGGING['exclude']['model']

    for excluded in excludes:
        if excluded in [instance._meta.app_label.lower(), instance.__class__.__name__.lower()] or instance.__module__.lower().startswith(excluded):
            return False

    return True


def get_current_user():
    """Get current user object from middleware"""
    thread_local = AutomatedLoggingMiddleware.thread_local
    if hasattr(thread_local, 'current_user'):
        user = thread_local.current_user
        if isinstance(user, AnonymousUser):
            user = None
    else:
        user = None

    return user


def get_current_environ():
    """Get current application and path object from middleware"""
    thread_local = AutomatedLoggingMiddleware.thread_local
    if hasattr(thread_local, 'request_uri'):
        request_uri = thread_local.request_uri
    else:
        request_uri = None

    if hasattr(thread_local, 'application'):
        application = thread_local.application
        application = Application.objects.get_or_create(name=application)[0]
    else:
        application = None

    if hasattr(thread_local, 'method'):
        method = thread_local.method
    else:
        method = None

    if hasattr(thread_local, 'status'):
        status = thread_local.status
    else:
        status = None

    return request_uri, application, method, status


def processor(status, sender, instance, updated=None, addition=''):
    """
    This is the standard logging processor.

    This is used to send the log to the handler and to other systems.
    """
    logger = logging.getLogger(__name__)
    if validate_instance(instance):
        user = get_current_user()
        application = instance._meta.app_label
        model_name = instance.__class__.__name__
        level = settings.AUTOMATED_LOGGING['loglevel']['model']

        if status == 'change':
            corrected = 'changed'
        elif status == 'add':
            corrected = 'added'
        elif status == 'delete':
            corrected = 'deleted'

        logger.log(level,
                   ('%s %s %s(%s) in %s%s' % (user, corrected, instance, model_name, application, addition)).replace("  ", " "),
                   extra={'action': 'model',
                          'data': {
                              'status': status,
                              'user': user,
                              'sender': sender,
                              'instance': instance,
                              'update_fields': updated
                          }
                          })
