=======================================
Django Database Based Automated Logging
=======================================
.. image:: https://img.shields.io/pypi/v/django-automated-logging.svg
  :target: https://pypi.python.org/pypi?name=django-automated-logging

.. image:: https://img.shields.io/pypi/l/django-automated-logging.svg
  :target: https://pypi.python.org/pypi?name=django-automated-logging

.. image:: https://img.shields.io/pypi/pyversions/django-automated-logging.svg
  :target: https://pypi.python.org/pypi?name=django-automated-logging

.. image:: https://travis-ci.org/indietyp/django-automated-logging.svg?branch=master
  :target: https://travis-ci.org/indietyp/django-automated-logging

.. image:: https://coveralls.io/repos/github/indietyp/django-automated-logging/badge.svg?branch=master
  :target: https://coveralls.io/github/indietyp/django-automated-logging?branch=master

.. image:: https://landscape.io/github/indietyp/django-automated-logging/master/landscape.svg?style=flat
  :target: https://landscape.io/github/indietyp/django-automated-logging/master
  :alt: Code Health

.. image:: https://api.codacy.com/project/badge/Grade/96fdb764fc34486399802b2f8267efcc
  :target: https://www.codacy.com/app/bilalmahmoud/django-automated-logging?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=indietyp/django-automated-logging&amp;utm_campaign=Badge_Grade

.. image:: https://img.shields.io/pypi/status/django-automated-logging.svg
  :target: https://pypi.python.org/pypi?name=django-automated-logging

Introduction
------------

Django Automated Logging - **finally** solved and done in a proper way.

*This package automaticially tracks, requests, model changes, requests - to a database or to another logger.*
**It is your choice what to do.**


What are the features?
----------------------
1. comes with an built-in database logger
2. easy to setup
3. extensible
4. feature-rich
5. many options to choose from - including the exclusion of certain packages, aswell as the disabling of database based logger
6. does what it needs to do - **nothing more**.
7. completely automated - nothing needs to be included from you, besides in the ``settings.py`` of your project.
8. This python package also catches logging messages unrelated to the package itself, if this is wanted - unrelated logging statements from e.g. your code, or djangos code can be catched. You just need to include the database handler to your handlers in ``LOGGING`` and enable the module ``unspecified``.


Setup
-----
Everything changed needs to be changed in the ``settings.py``

1. In the variable ``MIDDLEWARE`` append: ``'automated_logging.middleware.AutomatedLoggingMiddleware'``
2. In the variable ``INSTALLED_APPS`` append ``'automated_logging'``
3. In the variable ``LOGGING`` add in the ``handlers`` section (this is only required if you want database based logging):

   .. code:: python

    'db': {
        'level': 'INFO',
        'class': 'automated_logging.handlers.DatabaseHandler',
    }
4. In the variable ``LOGGING`` add to the ``loggers`` section (this is only required if you want database based logging):

   .. code:: python

    'automated_logging': {
        'level': 'INFO',
        'handlers': ['db'],
        'propagate': True,
    },
    'django': {
        'level': 'INFO',
        'handlers': ['db'],
        'propagate': True,
    },
5. `python3 manage.py migrate automated_logging`

``LOGGING`` attributes are just for recommondations and can be of course modified to your liking.


Configuration
-------------

You can configure the plugin by adding the variable ``AUTOMATED_LOGGING``
The defaults are, these can be partially overwritten

.. code:: python

    from logging import INFO
    AUTOMATED_LOGGING = {
        'exclude': ['Session', 'automated_logging', 'basehttp'],
        'modules': ['request', 'model', 'unspecified'],
        'to_database': True,
        'loglevel': {'model': INFO,
                     'request': INFO}
    }

In ``exclude`` ``automated_logging``, ``basehttp`` and ``admin`` are **recommended to be included** - due to potentially having multiple redundant logging entries.
Two modules are available: ``request`` and ``model``, these can be disabled, if needed.
The database integration can be - not recommended - be disabled. **The logger also needs to be disabled**.
The loglevel does indicate on which level things should be reported to other loggers, INFO or DEBUG is recommendend. Having ERROR or CRITICAL set is possible, but not recommended.
