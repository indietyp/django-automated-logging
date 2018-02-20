"""
This is where the magic happens.

This file contains the custom database based django ORM handler. This is just a bit hacky.
Some might even say this is just sorcery and magic.
"""
from logging import Handler


class DatabaseHandler(Handler):
    """Handler for logging into any database"""

    def __init__(self):
        super(DatabaseHandler, self).__init__()

    def emit(self, record):
        """
        Handler instance that records to the database. Heart of the project.

        try and except is preventing a circular import.
        Reference:
        http://stackoverflow.com/questions/4379042/django-circular-model-import-issue
        """
        try:
            from .models import Model, Application, ModelObject
            from django.contrib.contenttypes.models import ContentType

            if not hasattr(record, 'action'):
                from .settings import AUTOMATED_LOGGING

                signal = True
                for excluded in AUTOMATED_LOGGING['exclude']:
                    if record.module.startswith(excluded):
                        signal = False
                        break

                if 'unspecified' not in AUTOMATED_LOGGING['modules']:
                    signal = False

                if signal:
                    from .models import Unspecified

                    entry = Unspecified()

                    if hasattr(record, 'message'):
                        entry.message = record.message

                    entry.level = record.levelno
                    entry.file = record.pathname
                    entry.line = record.lineno

                    entry.save()

                return

            if record.action == 'model':
                if 'al_evt' in record.data['instance'].__dict__.keys():
                    entry = record.data['instance'].al_evt
                else:
                    entry = Model()
                    entry.user = record.data['user']
                    entry.save()

                    entry.application = Application.objects.get_or_create(name=record.data['instance']._meta.app_label)[0]

                    if hasattr(record, 'message'):
                        entry.message = record.message

                    if record.data['status'] == 'add':
                        status = 1
                    elif record.data['status'] == 'change':
                        status = 2
                    elif record.data['status'] == 'delete':
                        status = 3
                    else:
                        status = 0

                        from automated_logging.settings import AUTOMATED_LOGGING
                        if not AUTOMATED_LOGGING['save_na']:
                            entry.delete()

                            return None

                    entry.action = status
                    entry.information = ModelObject()
                    entry.information.value = repr(record.data['instance'])
                    ct = ContentType.objects.get_for_model(record.data['instance'])

                    try:
                        # check if the ContentType actually exists.
                        ContentType.objects.get(pk=ct.pk)
                        ct_exists = True
                    except ContentType.DoesNotExist:
                        ct_exists = False

                    if ct_exists:
                        entry.information.type = ct

                    entry.information.save()

                    record.data['instance'].al_evt = entry

                if 'al_chl' in record.data['instance'].__dict__.keys():
                    entry.modification = record.data['instance'].al_chl

                entry.save()

            elif record.action == 'request':
                from .models import Request

                if record.data['uri'] is not None:
                    entry = Request()
                    entry.application = record.data['application']
                    entry.uri = record.data['uri']
                    entry.user = record.data['user']
                    entry.status = record.data['status']
                    entry.method = record.data['method']
                    entry.save()

        except Exception as e:
            print(e)
