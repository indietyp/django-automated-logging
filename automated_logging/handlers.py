"""
This is where the magic happens.

This file contains the custom database based django ORM handler. This is just a bit hacky.
Some might even say this is just sorcery and magic.
"""
import datetime
import re

from django.utils import timezone
from logging import Handler


class DatabaseHandler(Handler):
    """Handler for logging into any database"""
    DURATION_RE = r'^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$'

    def __init__(self, maxage=None, *args, **kwargs):
        if maxage:
            matched = re.match(self.DURATION_RE, maxage)

            if matched:
                components = matched.groups()
                components = list(components)
                components.pop(4)

                adjusted = {'days': 0, 'seconds': 0}
                conversion = [['days', 365], ['days', 30], ['days', 7], ['days', 1],
                              ['seconds', 3600], ['seconds', 60], ['seconds', 1]]

                for pointer in range(len(components)):
                    if components[pointer]:
                        rate = conversion[pointer]
                        native = int(re.findall(r'(\d+)', components[pointer])[0])

                        adjusted[rate[0]] += native * rate[1]

                maxage = datetime.timedelta(**adjusted)
            else:
                print('Could not parse ISO8601 Duration string')

        self.maxage = maxage
        super(DatabaseHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        """
        Handler instance that records to the database.

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

                    if self.maxage:
                        current = timezone.now()
                        Unspecified.objects.filter(created_at__lte=current - self.maxage)\
                                           .delete()

                return

            if record.action == 'model':
                if ('al_evt' in record.data['instance'].__dict__.keys() and
                        record.data['instance'].al_evt):
                    entry = record.data['instance'].al_evt
                else:
                    entry = Model()
                    entry.user = record.data['user']
                    entry.save()

                    name = record.data['instance']._meta.app_label
                    entry.application = Application.objects.get_or_create(name=name)[0]

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
                    entry.information.value = repr(record.data['instance'])[:255]
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

                if ('al_chl' in record.data['instance'].__dict__.keys() and
                        record.data['instance'].al_chl and
                        not entry.modification):
                    entry.modification = record.data['instance'].al_chl

                entry.save()

                if self.maxage:
                    current = timezone.now()
                    Model.objects.filter(created_at__lte=current - self.maxage).delete()

            elif record.action == 'request':
                from .models import Request

                if record.data['uri'] is not None:
                    entry = Request()
                    entry.application = record.data['application']
                    entry.uri = record.data['uri'][:255]
                    entry.user = record.data['user']
                    entry.status = record.data['status']
                    entry.method = record.data['method']
                    entry.save()

                if self.maxage:
                    current = timezone.now()
                    Request.objects.filter(created_at__lte=current - self.maxage).delete()

        except Exception as e:
            print(e)
