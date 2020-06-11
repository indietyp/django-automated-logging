import re
from fnmatch import fnmatch
from typing import List

from automated_logging.models import RequestEvent
from automated_logging.settings import settings, Search


def valid_application(candidate: str, applications: List[Search]) -> bool:
    """
    Check if the candidate application string is valid with applications
    supplied by a list of ApplicationMatches.

    :param candidate: Django application
    :param applications: List of ApplicationStrings
    :return: valid?
    """

    for application in applications:
        match = False
        if application.type == 'glob':
            match = fnmatch(candidate, application.value)
        if application.type == 'plain':
            match = candidate == application.value
        if application.type == 'regex':
            match = bool(re.match(application.value, candidate))

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

    if event.application and valid_application(
        event.application.name, exclusions.applications
    ):
        return True

    if event.status in exclusions.status:
        return True

    if not event.application and exclusions.unknown:
        return True

    return False
