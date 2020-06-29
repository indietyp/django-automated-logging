import re
from fnmatch import fnmatch
from typing import List, Optional, Callable

from automated_logging.helpers import get_or_create_meta, get_or_create_local
from automated_logging.middleware import AutomatedLoggingMiddleware
from automated_logging.models import RequestEvent
from automated_logging.settings import settings, Search


def lazy_model_exclusion(instance) -> bool:
    """
    First look if the model has been excluded already
    -> only then look if excluded.
    """
    get_or_create_meta(instance)
    lazy = hasattr(instance._meta.dal, 'excluded')
    if not lazy:
        instance._meta.dal.excluded = model_exclusion(instance)

    return instance._meta.dal.excluded


def candidate_in_scope(candidate: str, scope: List[Search]) -> bool:
    """
    Check if the candidate string is valid with the scope supplied,
    the scope should be list of search strings - that can be either
    glob, plain or regex

    :param candidate: search string
    :param scope: List of Search
    :return: valid?
    """

    candidate = candidate.lower()
    for search in scope:
        match = False
        if search.type == 'glob':
            match = fnmatch(candidate, search.value)
        if search.type == 'plain':
            match = candidate == search.value
        if search.type == 'regex':
            match = bool(re.match(search.value, candidate, re.IGNORECASE))

        if match:
            return True

    return False


def request_exclusion(event: RequestEvent, function: Optional[Callable] = None) -> bool:
    """
    Determine if a request should be ignored/excluded from getting
    logged, these exclusions should be specified in the settings.

    :param event: RequestEvent
    :param function: Optional - function used by the resolver
    :return: should be excluded?
    """

    if function:
        get_or_create_local(AutomatedLoggingMiddleware.thread)
        ignored = getattr(AutomatedLoggingMiddleware.thread.dal, 'ignore.views', {})

        compiled = f'{function.__module__}.{function.__name__}'
        if (
            compiled in ignored
            # if ignored[compiled] is None, then no method will be ignored
            and ignored[compiled] is not None
            # ignored[compiled] == [] indicates all should be ignored
            and (len(ignored[compiled]) == 0 or event.method in ignored[compiled])
        ):
            return True

    exclusions = settings.request.exclude
    if event.method.lower() in exclusions.methods:
        return True

    if event.application and candidate_in_scope(
        event.application.name, exclusions.applications
    ):
        return True

    if event.status in exclusions.status:
        return True

    if not event.application and not exclusions.unknown:
        return True

    return False


def model_exclusion(instance) -> bool:
    """
    Determine if the instance of a model should be excluded,
    these exclusions should be specified in the settings.

    :param instance:
    :return: should be excluded?
    """

    if hasattr(instance.__class__, 'AutomatedLogging') and getattr(
        instance.__class__.AutomatedLogging, 'ignore', False
    ):
        return True

    exclusions = settings.model.exclude
    module = instance.__module__
    name = instance.__class__.__name__
    application = instance._meta.app_label

    if candidate_in_scope(name, exclusions.models) or candidate_in_scope(
        f'{module}.{name}', exclusions.models
    ):
        return True

    if candidate_in_scope(module, exclusions.models):
        return True

    if application and candidate_in_scope(application, exclusions.applications):
        return True

    # if there is no application string then we assume the model
    # location is unknown, if the flag unknown = False, then we just exclude
    if not application and not exclusions.unknown:
        return True

    return False


def field_exclusion(field: str, instance) -> bool:
    """
    Determine if the field of an instance should be excluded.
    """

    if hasattr(instance.__class__, 'AutomatedLogging') and field in getattr(
        instance.__class__.AutomatedLogging, 'ignore_fields', []
    ):
        return True

    exclusions = settings.model.exclude
    application = instance._meta.app_label
    model = instance.__class__.__name__

    if (
        candidate_in_scope(field, exclusions.fields)
        or candidate_in_scope(f'{model}.{field}', exclusions.fields)
        or candidate_in_scope(f'{application}.{model}.{field}', exclusions.fields)
    ):
        return True

    return False
