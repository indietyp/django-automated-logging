from automated_logging.settings import dev

urlpatterns = []

if dev:
    from automated_logging.tests.urls import urlpatterns as patterns

    urlpatterns.extend(patterns)
