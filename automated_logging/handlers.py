"""
    file containing the required handlers for logging to the database

    this is just basic sorcery
"""
from logging import Handler


class DatabaseHandler(Handler):
    """Handler for logging into any database"""
    def __init__(self):
        super(DatabaseHandler, self).__init__()

    def emit(self, record):
        # add to database
        # try - except -> preventing circular import
        # http://stackoverflow.com/questions/4379042/django-circular-model-import-issue

        try:
            from .models import Model, Application, ModelObject, ModelChangelog
            from django.contrib.contenttypes.models import ContentType

            if hasattr(record, 'action'):
                if record.action == 'model':
                    # print(record.data['instance'].__dict__)
                    entry = Model()
                    entry.user = record.data['user']
                    entry.application = Application.objects.get_or_create(name=record.data['instance']._meta.app_label)[0]

                    entry.message = record.message

                    if record.data['status'] == 'add':
                        status = 1
                    elif record.data['status'] == 'change':
                        status = 2
                    elif record.data['status'] == 'delete':
                        status = 3
                    else:
                        status = 0

                    entry.action = status
                    entry.information = ModelObject()
                    entry.information.value = repr(record.data['instance'])

                    entry.information.type = ContentType.objects.get_for_model(record.data['instance'])
                    entry.information.save()

                    if record.data['status'] == 'modified':
                        # print(record.data['instance'].__dict__)
                        if 'al_chl' in record.data['instance'].__dict__.keys():
                            entry.modification = record.data['instance'].al_chl
                    entry.save()

                    record.data['instance'].al_evt = entry

                elif record.action == 'request':
                    from .models import Request

                    entry = Request()
                    entry.application = record.data['application']
                    entry.request = record.data['uri']
                    entry.user = record.data['user']
                    entry.save()

            else:
                from .models import Unspecified

                entry = Unspecified()

                if hasattr(record, 'message'):
                    entry.message = record.message

                entry.level = record.levelno
                entry.file = record.pathname
                entry.line = record.lineno

                entry.save()
        except Exception as e:
            print(e)
            pass
