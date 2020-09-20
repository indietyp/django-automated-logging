from functools import wraps, partial
from typing import List, NamedTuple, Set, Optional

from automated_logging.helpers import (
    Operation,
    get_or_create_thread,
    function2path,
)
from automated_logging.helpers.enums import VerbOperationMap


def _normalize_view_args(methods: List[str]) -> Set[str]:
    if methods is not None:
        methods = {m.upper() for m in methods}

    return methods


# TODO: consider adding status_codes
def exclude_view(func=None, *, methods: Optional[List[str]] = ()):
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
        return partial(exclude_view, methods=methods)

    methods = _normalize_view_args(methods)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ simple wrapper """
        thread, _ = get_or_create_thread()

        path = function2path(func)
        if (
            path in thread.dal['ignore.views']
            and thread.dal['ignore.views'][path] is not None
            and methods is not None
        ):
            methods.update(thread.dal['ignore.views'][path])

        thread.dal['ignore.views'][path] = methods

        return func(*args, **kwargs)

    return wrapper


def include_view(func=None, *, methods: List[str] = None):
    """
    Decorator used for including specific views **regardless** if they
    are included in one of the exclusion patterns, this can be selectively done
    via methods. Non matching methods will still go through the exclusion pattern
    matching.

    :param func: function to be decorated
    :param methods: methods to be included (case-insensitive)
                    None => All methods will be explicitly included
                    [] => No method will be explicitly included
    :return: function
    """
    if func is None:
        return partial(include_view, methods=methods)

    methods = _normalize_view_args(methods)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ simple wrapper """
        thread, _ = get_or_create_thread()

        path = function2path(func)
        if (
            path in thread.dal['include.views']
            and thread.dal['include.views'][path] is not None
            and methods is not None
        ):
            methods.update(thread.dal['include.views'][path])

        thread.dal['include.views'][path] = methods
        return func(*args, **kwargs)

    return wrapper


def _normalize_model_args(
    operations: List[str], fields: List[str]
) -> [Set[Operation], Set[str]]:
    if operations is not None:
        operations = {
            VerbOperationMap[o.lower()]
            for o in operations
            if o.lower() in VerbOperationMap.keys()
        }

    if fields is not None:
        fields = set(fields)

    return operations, fields


IgnoreModel = NamedTuple(
    "IgnoreModel", (('operations', Set[Operation]), ('fields', Set[str]))
)


def exclude_model(
    func=None, *, operations: Optional[List[str]] = (), fields: List[str] = ()
):
    """
    Decorator used for ignoring specific models, without using the
    class or AUTOMATED_LOGGING configuration

    This is done via the local threading object. __module__ and __name__ are used
    to determine the right model.

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
        return partial(exclude_model, operations=operations, fields=fields)

    operations, fields = _normalize_model_args(operations, fields)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ simple wrapper """
        thread, _ = get_or_create_thread()
        path = function2path(func)

        if (
            path in thread.dal['ignore.models']
            and thread.dal['ignore.models'][path].operations is not None
            and operations is not None
        ):
            operations.update(thread.dal['ignore.models'][path].operations)

        if (
            path in thread.dal['ignore.models']
            and thread.dal['ignore.models'][path].fields is not None
            and fields is not None
        ):
            fields.update(thread.dal['ignore.models'][path].fields)

        thread.dal['ignore.models'][path] = IgnoreModel(operations, fields)

        return func(*args, **kwargs)

    return wrapper


IncludeModel = NamedTuple(
    "IncludeModel", (('operations', Set[Operation]), ('fields', Set[str]))
)


def include_model(func=None, *, operations: List[str] = None, fields: List[str] = None):
    """
    Decorator used for including specific models, despite potentially being ignored
    by the exclusion preferences set in the configuration.

    :param func: function to be decorated
    :param operations: operations to be ignored can be a list of:
                       modify, create, delete (case-insensitive)
                       [] => No operation will be explicitly included
                       None => All operations will be explicitly included
    :param fields: fields to be explicitly included
                   [] => No fields will be explicitly included
                   None => All fields will be explicitly included.

    :return: function
    """
    if func is None:
        return partial(include_model, operations=operations, fields=fields)

    operations, fields = _normalize_model_args(operations, fields)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """ simple wrapper """
        thread, _ = get_or_create_thread()
        path = function2path(func)

        if (
            path in thread.dal['include.models']
            and thread.dal['include.models'][path].operations is not None
            and operations is not None
        ):
            operations.update(thread.dal['include.models'][path].operations)

        if (
            path in thread.dal['include.models']
            and thread.dal['include.models'][path].fields is not None
            and fields is not None
        ):
            fields.update(thread.dal['include.models'][path].fields)

        thread.dal['include.models'][path] = IncludeModel(operations, fields)

        return func(*args, **kwargs)

    return wrapper
