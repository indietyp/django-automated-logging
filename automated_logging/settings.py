from django.conf import settings as st
from logging import INFO

DEFAULT_AUTOMATED_LOGGING = {
    'exclude': {'model': ['Session', 'automated_logging', 'basehttp'],
                'request': [],
                'unspecified': []},
    'modules': ['request', 'model', 'unspecified'],
    'to_database': True,
    'loglevel': {'model': INFO,
                 'request': INFO},
    'save_na': True,
}


def auto_complete(setting, default):
  for k, v in default.items():
    if k not in setting.keys():
      setting[k] = v
    elif isinstance(setting[k], dict):
      setting[k] = auto_complete(setting[k], default[k])
    elif isinstance(setting[k], str):
      setting[k] = setting[k].lower()

  return setting


if hasattr(st, 'AUTOMATED_LOGGING'):
  AUTOMATED_LOGGING = auto_complete(st.AUTOMATED_LOGGING, DEFAULT_AUTOMATED_LOGGING)
else:
  AUTOMATED_LOGGING = DEFAULT_AUTOMATED_LOGGING
