"""
WSGI config for logtest project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logtest.settings")

# import sys
# from django.conf import settings
# sys.path.append(os.path.dirname(settings.BASE_DIR))
application = get_wsgi_application()
