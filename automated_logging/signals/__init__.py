from automated_logging.models import RequestEvent
from automated_logging.settings import settings


def request_exclusion(event: RequestEvent) -> bool:
    """
    Determine if a request should be ignored/excluded from getting
    logged, these exclusions should be specified in the settings.
    """

    exclusions = settings.request.exclude
    if event.method.lower() in exclusions.methods:
        return True

    # TODO: exclude application

    if event.status in exclusions.status:
        return True

    if not event.application and exclusions.unknown:
        return True

    return False
