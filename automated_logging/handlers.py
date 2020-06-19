from datetime import datetime
from logging import Handler, LogRecord
from typing import Dict, Any, TYPE_CHECKING

from django.db.models import ForeignObject, Model
from django.db.models.fields.reverse_related import ForeignObjectRel

if TYPE_CHECKING:
    # we need to do this, to avoid circular imports
    from automated_logging.models import RequestEvent


class DatabaseHandler(Handler):
    def __init__(self, max_age=None, *args, **kwargs):
        # TODO: maxage and max_age
        # TODO: batch
        super(DatabaseHandler, self).__init__(*args, **kwargs)

    def prepare_save(self, instance: Model):
        """
        Due to the nature of all modifications and such there are some models
        that are in nature get_or_create and not creations
        (we don't want so much additional data)

        This is a recursive function that looks for relationships and
        replaces specific values with their get_or_create counterparts.

        :param instance: model
        :return: instance that is suitable for saving
        """
        from automated_logging.models import Application, ModelMirror, ModelField

        if isinstance(instance, Application):
            return Application.objects.get_or_create(name=instance.name)[0]
        elif isinstance(instance, ModelMirror):
            return ModelMirror.objects.get_or_create(
                name=instance.name, application=self.prepare_save(instance.application)
            )[0]
        elif isinstance(instance, ModelField):
            return ModelField.objects.get_or_create(
                name=instance.name,
                model=self.prepare_save(instance.model),
                type=instance.type,
            )[0]

        for field in [
            f
            for f in instance._meta.get_fields()
            if isinstance(f, (ForeignObjectRel, ForeignObject))
            and getattr(instance, f.name, None) is not None
        ]:
            setattr(
                instance, field.name, self.prepare_save(getattr(instance, field.name))
            )

        return instance

    def unspecified(self, record: LogRecord) -> None:
        pass

    def model(self, record: LogRecord, data: Dict[str, Any]) -> None:
        pass

    def m2m(self, record: LogRecord, data: Dict[str, Any]) -> None:
        pass

    def request(self, record: LogRecord, event: 'RequestEvent') -> None:
        """
        The request event already has a model prepared that we just
        need to prepare and save.

        :param record: LogRecord
        :param event: Event supplied via the LogRecord
        :return: nothing
        """

        self.prepare_save(event).save()

    def emit(self, record: LogRecord) -> None:
        if not hasattr(record, 'action'):
            return self.unspecified(record)

        if record.action == 'model':
            return self.model(record, record.data)
        elif record.action == 'model[m2m]':
            return self.m2m(record, record.data)
        elif record.action == 'request':
            return self.request(record, record.event)
