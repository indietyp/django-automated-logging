import re
from fnmatch import fnmatch
from typing import List

from automated_logging.models import RequestEvent
from automated_logging.settings import settings, Search


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


def create_meta(instance) -> None:
    """
    Simple helper function that created the dal object
    in the meta container.

    :param instance:
    :return:
    """
    if not hasattr(instance._meta, 'dal'):
        instance._meta.dal = MetaDataContainer()


def lazy_model_exclusion(instance) -> bool:
    """
    First look if the model has been excluded already
    -> only then look if excluded.
    """
    create_meta(instance)
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

    for search in scope:
        match = False
        if search.type == 'glob':
            match = fnmatch(candidate, search.value)
        if search.type == 'plain':
            match = candidate == search.value
        if search.type == 'regex':
            match = bool(re.match(search.value, candidate))

        if match:
            return True

    return False


def request_exclusion(event: RequestEvent) -> bool:
    """
    Determine if a request should be ignored/excluded from getting
    logged, these exclusions should be specified in the settings.

    :param event: RequestEvent
    :return: should be excluded?
    """

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

    if candidate_in_scope(name, exclusions.models):
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


def field_exclusion(instance) -> bool:
    pass
