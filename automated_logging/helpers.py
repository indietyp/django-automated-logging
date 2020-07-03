"""
Helpers that are used throughout django-automated-logging
"""

from collections import namedtuple
from enum import Enum
from typing import Any

from automated_logging.middleware import AutomatedLoggingMiddleware


class Operation(int, Enum):
    """
    Simple Enum that will be used across the code to
    indicate the current operation that happened.

    Due to the fact that enum support for django was
    only added in 3.0 we have DjangoOperations to convert
    it to the old django format.
    """

    CREATE = 1
    MODIFY = 0
    DELETE = -1


DjangoOperations = [(e.value, o.lower()) for o, e in Operation.__members__.items()]


def namedtuple2dict(root: namedtuple) -> dict:
    """
    transforms nested namedtuple into a dict

    :param root: namedtuple to convert
    :return: dictionary from namedtuple
    """
    return {
        k: v if not isinstance(v, tuple) else namedtuple2dict(v)
        for k, v in root._asdict().items()
    }


def get_or_create_meta(instance) -> [Any, bool]:
    """
    Simple helper function that created the dal object
    in the meta container.

    :param instance:
    :return:
    """
    return instance, get_or_create_local(instance._meta)


def get_or_create_thread() -> [Any, bool]:
    """
    Get or create the local thread, will always return False as the thread
    won't be created, but the local dal object will.

    get_or_create to conform with the other functions.

    :return: thread, created dal object?
    """
    thread = AutomatedLoggingMiddleware.thread

    # TODO: consider renaming
    return (
        thread,
        get_or_create_local(
            thread,
            {
                'ignore.views': dict,
                'ignore.models': dict,
                'include.views': dict,
                'include.models': dict,
            },
        ),
    )


def get_or_create_local(target: Any, defaults={}) -> bool:
    """
    Get or create local storage DAL metadata container where dal specific data is.

    :return: created?
    """

    if not hasattr(target, 'dal'):
        target.dal = MetaDataContainer(defaults)
        return True

    return False


def function2path(func):
    """ simple helper function to return the module path of a function """
    return f'{func.__module__}.{func.__name__}'


class MetaDataContainer(dict):
    """
    simple class we use, to store values.

    Values can be retrieved via attribute or item.
    """

    def __init__(self, defaults={}):
        super().__init__()

        self.auto = defaults

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            if item in self.auto:
                self[item] = self.auto[item]()
                return self[item]
            else:
                raise KeyError

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value):
        self[key] = value
