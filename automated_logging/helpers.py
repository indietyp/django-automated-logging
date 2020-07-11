"""
Helpers that are used throughout django-automated-logging
"""

from collections import namedtuple
from datetime import datetime
from enum import Enum
from typing import Any, Tuple

from automated_logging.middleware import AutomatedLoggingMiddleware
from automated_logging.settings import settings


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


# should these be maybe lower-cased?
DjangoOperations = [(e.value, o.lower()) for o, e in Operation.__members__.items()]

VerbOperationMap = {
    'create': Operation.CREATE,
    'modify': Operation.MODIFY,
    'delete': Operation.DELETE,
    'add': Operation.CREATE,
    'remove': Operation.DELETE,
}

VerbM2MOperationMap = {
    'add': Operation.CREATE,
    'modify': Operation.MODIFY,
    'remove': Operation.DELETE,
}

PastOperationMap = {
    'created': Operation.CREATE,
    'modified': Operation.MODIFY,
    'deleted': Operation.DELETE,
}

PastM2MOperationMap = {
    'added': Operation.CREATE,
    'modified': Operation.MODIFY,
    'removed': Operation.DELETE,
}

ShortOperationMap = {
    '+': Operation.CREATE,
    '~': Operation.MODIFY,
    '-': Operation.DELETE,
}

TranslationOperationMap = {**VerbOperationMap, **PastOperationMap, **ShortOperationMap}


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
    Simple helper function that creates the dal object
    in _meta.

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


def get_or_create_local(target: Any, defaults={}, key='dal') -> bool:
    """
    Get or create local storage DAL metadata container,
    where dal specific data is.

    :return: created?
    """

    if not hasattr(target, key):
        setattr(target, key, MetaDataContainer(defaults))
        return True

    return False


def get_or_create_model_event(instance, force=False, extra=False) -> [Any, bool]:
    """
    Get or create the ModelEvent of an instance.
    This function will also populate the event with the current information.

    :param instance: instance to derive an event from
    :param force: force creation of new event?
    :param extra: extra information inserted?
    :return: [event, created?]
    """
    from automated_logging.models import (
        ModelEvent,
        ModelEntry,
        ModelMirror,
        Application,
    )

    get_or_create_meta(instance)

    if hasattr(instance._meta.dal, 'event') and not force:
        return instance._meta.dal.event, False

    instance._meta.dal.event = None

    event = ModelEvent()
    event.user = AutomatedLoggingMiddleware.get_current_user()

    if settings.model.snapshot and extra:
        event.snapshot = instance

    if (
        settings.model.performance
        and hasattr(instance._meta.dal, 'performance')
        and extra
    ):
        event.performance = datetime.now() - instance._meta.dal.performance

    event.model = ModelEntry()
    event.model.model = ModelMirror()
    event.model.model.name = instance.__class__.__name__
    event.model.model.application = Application(name=instance._meta.app_label)
    event.model.value = repr(instance) or str(instance)
    event.model.primary_key = instance.pk

    instance._meta.dal.event = event

    return instance._meta.dal.event, True


def function2path(func):
    """ simple helper function to return the module path of a function """
    return f'{func.__module__}.{func.__name__}'


class MetaDataContainer(dict):
    """
    MetaDataContainer is used to store DAL specific metadata
    in various places.

    Values can be retrieved via attribute or key retrieval.

    A dictionary with key attributes can be provided when __init__.
    The key should be the name of the item, the value should be a function
    that gets called when an item with that key does
    not exist gets accessed, to auto-initialize that key.
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
