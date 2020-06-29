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

``LOGGING`` attributes are just for recommendations and can be of course modified to your liking.


Configuration
-------------

You can configure the plugin by adding the variable ``AUTOMATED_LOGGING``
The defaults are present in the example.

.. code:: python

    from logging import INFO
    AUTOMATED_LOGGING = {
        'model': {
            'detailed_message': True,
            'exclude': {
                'applications': [
                    'session',
                    'automated_logging',
                    'admin',
                    'basehttp',
                    'migrations',
                    'contenttypes',
                ],
                'fields': [],
                'models': [],
                'unknown': False,
            },
            'loglevel': INFO,
            'mask': [],
            'performance': False,
            'snapshot': False,
            'user_mirror': False,
        },
        'modules': ['request', 'model', 'unspecified'],
        'request': {
            'data': {
                'content_types': ['application/json'],
                'enabled': [],
                'ignore': [],
                'mask': ['password'],
                'query': False,
            },
            'exclude': {
                'applications': [],
                'methods': ['GET'],
                'status': [200],
                'unknown': False,
            },
            'loglevel': INFO,
        },
        'unspecified': {
            'exclude': {'applications': [], 'files': [], 'unknown': False},
            'loglevel': INFO,
        },
    }


You can always inspect the current default configuration by importing ``from automated_logging.settings import default``.

**It is recommended** to include the application defaults for ``model.exclude`` due to potentially having multiple redundant logging entries and to disable applied migrations and session operations.

There are three independent modules available: ``request``, ``unspecified`` and ``model``, these
can be enabled and disabled if needed via the ``modules`` setting.

The ``loglevel`` setting indicated the severity for the sent messages.
INFO or DEBUG are usually the right call.

*New in version 5.x.x:* You can now specify a maximum age for database entries created via ``maxage`` in the ``LOGGING`` variable. maxage needs to be an `ISO8601 duration string <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_.

*New in version 6.x.x* To disable the database integrations just remove the handler.

*New in version 6.x.x* You can now specify the maximum age as ``maxage`` *and* ``max_age`` and also as ``timedelta()``

*New in version 6.x.x* You can batch saving objects via ``batching`` in the ``LOGGING`` variable. ``batching`` should be an ``int`` and indicates the threshold number of objects that are to be saved batched. Specifying ``batching`` can lead to data loss!

*New in version 6.x.x* ``applications``, ``models`` can now be specified as regex or glob and are as default interpreted as glob. You can "select" which method to use by prefixing the item with ``gl:`` for glob or ``re:`` for regex. You can disable glob or regex by prefixing it with ``pl:``.

Decorators
----------
*New in version 6.x.x*

Class-Based Configuration
-------------------------
*New in version 6.x.x*

TODO: operations

Changelog
=========
Version 6.0.0
-------------
- **Added:** ``max_age``, ``batching`` settings to the handler
- **Added:** decorators
- **Added:** class-based configuration
- **Added:** request and response bodies can now be saved
- **Added:** regex, glob matching for settings
- **Updated:** settings
- **Updated:** models
- **Updated:** to current django version (2.2 and 3.0)
- **Updated:** DAL no longer stores internal information directly, but now has a custom _meta object injected.
- **Updated:** project now uses black for formatting
- **Updated:** internals were completely rewritten for greater maintainability and speed.
- **Fixed:** https://github.com/indietyp/django-automated-logging/issues/1
- **Fixed:** https://github.com/indietyp/django-automated-logging/issues/2

Version 5.0.0
-------------
- **Added:** ``maxage`` handler setting to automatically remove database entries after a certain amount of time.
- **Added:** query string in requests can now be enabled/disabled (are now disabled by default)
- **Fixed:** Value and URI could be longer than 255 characters. DAL would throw an exception. This is fixed.

Roadmap
=======
Version 7.x.x
-------------
- ☐ implementation of an git like versioning interface

Version 8.x.x
-------------
- ☐ temporary world domination