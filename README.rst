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
It is simple just ``pip3 install django-automated-logging``.

Introduction
------------
Django Automated Logging - **finally** solved and done in a proper way.

What is the purpose?
--------------------
The goal of the django application is it to provide an easy and accesible way to log. So that you do not need to reinvent the whell over and over.
The application is written to only use minimal requirements - which is just Django currently.

How does it work?
-----------------
This application uses a custom logging handler - called DatabaseHandler which instead of outputting it into a file just outputs everything through the Django ORM.
It knows how to do so by using signals - that are provided by Django itself and annotating the actual model object with the changelog.

This enables us to actually also monitor Many-Two-Many changes, which are kinda tricky to do so.

Wait!
-----
What if I just want to log the changes but to a file and not to a database?

This is very understandable and also something that is possible without a problem, because we exclude the actual database portion to a handler you can just use a file logger instead, because this module uses native logging statesments and extra paramenters - you can actually - quite easily build you own logger and access them in a formatting statement in the logger. Pretty neat, huh?


So in a nutshell this package **automaticially** tracks *requests, model changes and every other message* - to a database or to another logger.
**It is your choice what to do.**


====================
Detailed Information
====================

Features
--------
1. easy to setup
2. extensible
3. feature-rich
4. completely automated
5. comes with an built-in database logger
6. no custom code needs to be inserted into your codebase
7. catches logging messages unrelated to the package itself if desired
8. does what it needs to do - **nothing more**.


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
The defaults are present in the example.

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
Three modules are available: ``request``, ``unspecified`` and ``model``, these can be disabled, if needed.
The database integration can be disabled. *Note: the handler than also needs to be removed*.
The loglevel does indicate on which level things should be reported to other handlers, INFO or DEBUG is recommendend. Having ERROR or CRITICAL set is possible, but not recommended.

=======
Roadmap
=======

Version 6.0.0
-------------
- remove the LDAP model
- exclusion for also unspecified and request
- implement requested features
