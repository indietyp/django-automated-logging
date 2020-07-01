"""
Helpers that are used throughout django-automated-logging
"""

from collections import namedtuple
from enum import Enum
from typing import Any


class Operation(Enum):
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


def get_or_create_meta(instance) -> bool:
    """
    Simple helper function that created the dal object
    in the meta container.

    :param instance:
    :return:
    """
    return get_or_create_local(instance._meta)


def get_or_create_local(target: Any) -> bool:
    """
    Get or create local storage DAL metadata container where dal specific data is.

    :return: created?
    """

    if not hasattr(target, 'dal'):
        target.dal = MetaDataContainer()
        return True

    return False


class MetaDataContainer(dict):
    """
    simple class we use, to store values.

    Values can be retrieved via attribute or item.
    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value):
        self[key] = value
