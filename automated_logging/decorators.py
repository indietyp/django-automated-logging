import random
import threading
from collections import namedtuple
from functools import wraps, partial
from typing import List, NamedTuple, Any, Optional

from automated_logging.helpers import get_or_create_local, Operation
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
    if methods is not None:
        methods = set(methods)

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
        path = f'{func.__module__}.{func.__name__}'
        if (
            path in thread.dal['ignore.views']
            and isinstance(thread.dal['ignore.views'][path], set)
            and methods is not None
        ):
            methods.update(thread.dal['ignore.views'][path])

        thread.dal['ignore.views'][path] = (
            None if methods is None else {m.upper() for m in methods}
        )

        return func(*args, **kwargs)

    return wrapper


IgnoreModel = NamedTuple(
    "IgnoreModel", (('operations', List[Operation]), ('fields', List[str]))
)


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
        """ simple wrapper """
        thread = AutomatedLoggingMiddleware.thread
        get_or_create_local(thread)

        if 'ignore.models' not in thread.dal:
            thread.dal['ignore.models'] = {}

        thread.dal['ignore.models'][f'{func.__module__}.{func.__name__}'] = {}

    return wrapper
