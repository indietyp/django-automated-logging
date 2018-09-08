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

.. image:: https://img.shields.io/badge/Support%20the%20Project-PayPal-green.svg
  :target: https://paypal.me/indietyp/5

What is DAL?
============
In a nutshell, this package **automatically** tracks *requests, model changes, and every other message supplied* - to a database or to another logger.
**It is your choice what to do.**

Introduction
------------
Django Automated Logging - **finally** solved and done in a proper way.

How to install? It is simple just ``pip3 install django-automated-logging``.

What is the purpose?
--------------------
The goal of the django application is it to provide an easy and accessible way to log. Therefore you do not need to reinvent the wheel over and over.
The application is written to use minimal requirements - which is just Django currently.

How does it work?
-----------------
This application uses a custom logging handler - called DatabaseHandler. Instead of outputting it into a file, it outputs everything through the Django ORM.
It knows how to do so by using signals - that are provided by Django itself and annotating the actual model object with the changelog.

This enables us to actually monitor Many-Two-Many changes, which are kind of tricky.

Wait!
-----
What if I just want to log the changes to a file and not to a database?

This is very understandable. It is possible without a problem because we exclude the actual database portion to a handler. You can just use a file logger instead. This module uses native logging statements and extra paramenters. You can easily build your own logger and access them in a formatting statement in the logger. Pretty neat, huh?

Detailed Information
====================

Features
--------
1. Easy to setup
2. Extensible
3. Feature-rich
4. Completely automated
5. Comes with an built-in database logger
6. No custom code needs to be inserted into your codebase
7. Catches logging messages unrelated to the package itself if desired
8. Does what it needs to do - **nothing more**.


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
        'exclude': {'model': ['Session', 'automated_logging', 'basehttp'],
                    'request': ['GET', 200],
                    'unspecified': []},
        'modules': ['request', 'model', 'unspecified'],
        'to_database': True,
        'loglevel': {'model': INFO,
                     'request': INFO},
        'save_na': True,
    }

In ``exclude`` ``automated_logging``, ``basehttp`` and ``admin`` are **recommended to be included** - due to potentially having multiple redundant logging entries.
Three modules are available: ``request``, ``unspecified`` and ``model``, these can be disabled, if needed.
The database integration can be disabled. *Note: the handler than also needs to be removed*.
The loglevel does indicate on which level things should be reported to other handlers, INFO or DEBUG is recommendend. Having ERROR or CRITICAL set is possible, but not recommended.

*New in version 4.x.x:* **all strings** in ``AUTOMATED_LOGGING`` are case-insensitive.

Roadmap
=======

Version 4.0.0
-------------
[ ] remove the LDAP model
[x] exclusion for request module
[ ] exclusion for unspecified module
[ ] implement requested features
[ ] adding options to Meta field
--> ignored fields
--> ignored operations
[ ] prevent migration logs

Version 5.0.0
-------------
[ ] implementation of an git like versioning interface
[ ] performance considerations

Version 6.0.0
-------------
[ ] temporary world domination


Support the Project
