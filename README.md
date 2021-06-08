# Django Database Based Automated Logging

[![](https://badgen.net/pypi/v/django-automated-logging)](https://pypi.python.org/pypi?name=django-automated-logging)
[![](https://badgen.net/pypi/license/django-automated-logging)](https://pypi.python.org/pypi?name=django-automated-logging)
[![](https://img.shields.io/pypi/status/django-automated-logging.svg)](https://pypi.python.org/pypi?name=django-automated-logging)
[![](https://badgen.net/pypi/python/django-automated-logging)](https://pypi.python.org/pypi?name=django-automated-logging)
[![Build Status](https://www.travis-ci.com/indietyp/django-automated-logging.svg?branch=master)](https://www.travis-ci.com/indietyp/django-automated-logging)
[![](https://coveralls.io/repos/github/indietyp/django-automated-logging/badge.svg?branch=master)](https://coveralls.io/github/indietyp/django-automated-logging?branch=master)
[![](https://api.codacy.com/project/badge/Grade/96fdb764fc34486399802b2f8267efcc)](https://www.codacy.com/app/bilalmahmoud/django-automated-logging?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=indietyp/django-automated-logging&amp;utm_campaign=Badge_Grade)
[![](https://img.shields.io/badge/Support%20the%20Project-PayPal-green.svg)](https://paypal.me/indietyp/5)

**Notice:** Most of this will be moved into a wiki.

## What is Django-Automated-Logging (DAL)?

TL;DR: DAL is a package to **automatically** track changes in your project, ranging
from simple logging messages, to model changes or requests done by users.

You can decide what you want to do and how.
DAL allows fine-grained customization and filtering with various methods.

### Introduction

Django Fully Automated Logging - **finally** solved and done properly.

How to install?
`pip install django-automated-logging` or `poetry add django-automated-logging`

### What is the purpose?
The goal of DAL is to provide an easy, accessible and DRY way to log the inner working of you applications.
Ultimately giving you the chance to easily see what is happening without excessive manual print/logging statements.

The application uses minimal requirements and is performant.

### How does it work?
The application facilitates the built-in logging mechanic
by providing a custom handler, that just needs to be added to the `LOGGING` configuration.

DAL uses native Django signals to know what is happening behind the scenes without injecting custom code.

### Minimal Setup

You can also configure DAL to only log to a file and not to a database.
You just need to enable DAL and not include the custom logging handler.

## Detailed Information

### Features

1. Easy Setup
2. Extensible
3. Feature-Rich
4. Completely Automated
5. Built-In Database Logger
6. No custom code needs to be inserted into your codebase
7. Can capture logging messages unrelated to the package itself
8. Only does what it needs to do, no extra bells and whistles.

### Setup

Initial Configuration is via your projects `settings.py`

1. `INSTALLED_APPS` append: `'automated_logging'`
2. `MIDDLEWARE` append: `'automated_logging.middleware.AutomatedLoggingMiddleware'`
3. `LOGGING` section `handlers` add:
    ```python
       'db': {
           'level': 'INFO',
           'class': 'automated_logging.handlers.DatabaseHandler',
       }
    ```
4. `LOGGING` section `loggers` add: (only required if database logging desired)
    ```python
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
    ```
5. execute: `python manage.py migrate automated_logging`

`LOGGING` configuration details are just recommendations.

### Configuration

Further configuration can be done via the variable `AUTOMATED_LOGGING`. The defaults are:

```python
AUTOMATED_LOGGING = {
    "globals": {
        "exclude": {
            "applications": [
                "plain:contenttypes",
                "plain:admin",
                "plain:basehttp",
                "glob:session*",
                "plain:migrations",
            ]
        }
    },
    "model": {
        "detailed_message": True,
        "exclude": {"applications": [], "fields": [], "models": [], "unknown": False},
        "loglevel": 20,
        "mask": [],
        "max_age": None,
        "performance": False,
        "snapshot": False,
        "user_mirror": False,
    },
    "modules": ["request", "unspecified", "model"],
    "request": {
        "data": {
            "content_types": ["application/json"],
            "enabled": [],
            "ignore": [],
            "mask": ["password"],
            "query": False,
        },
        "exclude": {
            "applications": [],
            "methods": ["GET"],
            "status": [200],
            "unknown": False,
        },
        "ip": True,
        "loglevel": 20,
        "max_age": None,
    },
    "unspecified": {
        "exclude": {"applications": [], "files": [], "unknown": False},
        "loglevel": 20,
        "max_age": None,
    },
}
```

You can always inspect the current default configuration by doing:

```python
from pprint import pprint
from automated_logging.settings import default
from automated_logging.helpers import namedtuple2dict

pprint(namedtuple2dict(default))
```

**Recommendation:** include the `globals` application defaults as those modules can be particularly verbose or be duplicates.

There are *three* different independent modules available `request` (for request logging), `unspecified` (for general logging messages), and `models` (for model changes).
They can be enabled and disabled by including them in the `modules` configuration.

The `loglevel` setting indicates the severity for the logging messages sent from the module.
`INFO (20)` or `DEBUG (10)` is the right call for most cases.

*New in 6.x.x:* Saving can be batched via the `batch` setting for the handler.

*New in 6.x.x:* Saving can be threaded by `thread: True` for the handler settings. **This is highly experimental**

*New in 6.x.x:* every field in `exclude` can be either be a `glob` (prefixing the string with `gl:`), a `regex` (prefixing the string with `re:`) or plain (prefixing the string with `pl:`). The default is `glob`.

### Decorators

You can explicitly exclude or include views/models, by using the new decorators.

```python
from automated_logging.decorators import include_view, include_model, exclude_view, exclude_model

@include_view(methods=None)
@exclude_view(methods=[])
def view(request):
    pass

@include_model(operations=None, fields=None)
@exclude_model(operations=[], fields=[])
class ExampleModel:
    pass
```

`include` *always* takes precedence over `exclude`, if you use multiple `include` or `exclude` instead of overwriting they will *update/extend* the previous definition.

`operations` can be either `create`, `modify`, `delete`. `fields` is a list model specific fields to be included/excluded.
`methods` is a list methods to be included/excluded.

### Class-Based Configuration

Class-Based Configuration is done over a specific meta class `LoggingIgnore`. Decorators take precedence over class-based configuration, but class-based configuration takes precedence over AUTOMATED_LOGGING configuration.

```python
class ExampleModel:
    class LoggingIgnore:
        complete = False
        fields = []
        operations = []
```

as described above `operations` and `fields` work the same way. `complete = True` means that a model is excluded no matter what.

## Changelog

### Version 6.0.0
- **Added:** ``batch`` settings to the handler
- **Added:** decorators
- **Added:** class-based configuration
- **Added:** request and response bodies can now be saved
- **Added:** regex, glob matching for settings
- **Updated:** settings
- **Updated:** models
- **Updated:** to current django version (2.2, 3.0, 3.1)
- **Updated:** DAL no longer stores internal information directly, but now has a custom _meta object injected.
- **Updated:** project now uses black for formatting
- **Updated:** internals were completely rewritten for greater maintainability and speed.
- **Fixed:** https://github.com/indietyp/django-automated-logging/issues/1
- **Fixed:** https://github.com/indietyp/django-automated-logging/issues/2
- **Moved:** `max_age` is now part of the `settings.py` configuration.

### Version 5.0.0
- **Added:** ``maxage`` handler setting to automatically remove database entries after a certain amount of time.
- **Added:** query string in requests can now be enabled/disabled (are now disabled by default)
- **Fixed:** Value and URI could be longer than 255 characters. DAL would throw an exception. This is fixed.


## Roadmap

### Version 6.1.x
- [ ] archive options
- [ ] decorators greater flexibility
- [ ] wiki -> documentation
- [ ] make django-ipware optional via extras
- [ ] and more!

### Version 7.x.x
- [ ] implementation of a git like versioning interface

### Version 8.x.x
- [ ] temporary world domination
