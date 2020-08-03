"""
Automated Logging specific views,
currently unused except for testing redirection
"""

from automated_logging.settings import dev

if dev:
    from automated_logging.tests.views import *
