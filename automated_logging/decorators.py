import threading
from collections import namedtuple
from functools import wraps, partial
from typing import List, NamedTuple, Any, Optional

from automated_logging.helpers import get_or_create_local
from automated_logging.middleware import AutomatedLoggingMiddleware


# def ignore(func=None, *, model: bool = False, view: bool = False):
#     if func is None:
#         return partial(ignore, model)
#
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         pass
#
#     return wrapper


def ignore_view(func=None, *, methods: List[str] = ()):
    """
    Decorator used for ignoring specific views, without adding them
    to the AUTOMATED_LOGGING configuration.

    This is done via the local threading object. This is done via the function
    name and module location.

    :param func: function to be decorated
    :param methods: methods to be ignored (case-insensitive),
                    None => No method will be ignored,
                    [] => All methods will be ignored

    :return: function
    """
    if func is None:
        return partial(ignore_view, methods=methods)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ simple wrapper """
        thread = AutomatedLoggingMiddleware.thread
        get_or_create_local(thread)

        if 'ignore.views' not in thread.dal:
            thread.dal['ignore.views'] = {}

        # this should work in theory as it points to the function from the module
        # I am not completely sure if it does tho.
        thread.dal['ignore.views'][f'{func.__module__}.{func.__name__}'] = (
            [m.upper() for m in methods] if methods is not None else None
        )

        return func(*args, **kwargs)

    return wrapper


def ignore_model(func=None, *, operations: List[str] = (), fields: List[str] = None):
    """
    Decorator used for ignoring specific models, without using the
    class or AUTOMATED_LOGGING configuration

    This is done via the local threading object. __module__ and __name__ are used
    to determine the right model.

    TODO: consider (+, -, ~)

    :param func: function to be decorated
    :param operations: operations to be ignored can be a list of:
                       modify, create, delete (case-insensitive)
                       [] => All operations will be ignored
                       None => No operation will be ignored
    :param fields: fields to be ignored in not ignored operations
                   [] => All fields will be ignored
                   None => No field will be ignored
    :return: function
    """
    if func is None:
        return partial(ignore_model, operations=operations, fields=fields)

    @wraps(func)
    def wrapper(*args, **kwargs):
        pass

    return wrapper
