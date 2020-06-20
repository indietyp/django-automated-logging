from datetime import datetime
from logging import Handler, LogRecord
from typing import Dict, Any, TYPE_CHECKING, List

from django.db.models import ForeignObject, Model
from django.db.models.fields.reverse_related import ForeignObjectRel

if TYPE_CHECKING:
    # we need to do this, to avoid circular imports
    from automated_logging.models import (
        RequestEvent,
        ModelEvent,
        ModelValueModification,
    )


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
        from automated_logging.models import (
            Application,
            ModelMirror,
            ModelField,
            ModelEntry,
        )

        if isinstance(instance, Application):
            return Application.objects.get_or_create(name=instance.name)[0]
        elif isinstance(instance, ModelMirror):
            return ModelMirror.objects.get_or_create(
                name=instance.name, application=self.prepare_save(instance.application)
            )[0]
        elif isinstance(instance, ModelField):
            entry = ModelField.objects.get_or_create(
                name=instance.name, model=self.prepare_save(instance.model)
            )[0]
            entry.type = instance.type
            return entry
        elif isinstance(instance, ModelEntry):
            entry = ModelEntry.objects.get_or_create(
                model=self.prepare_save(instance.model),
                primary_key=instance.primary_key,
            )[0]
            entry.value = instance.value
            return entry

        for field in [
            f
            for f in instance._meta.get_fields()
            if isinstance(f, ForeignObject)
            and getattr(instance, f.name, None) is not None
        ]:
            setattr(
                instance, field.name, self.prepare_save(getattr(instance, field.name))
            )

        # ForeignObjectRel is untouched rn

        return instance

    def unspecified(self, record: LogRecord) -> None:
        pass

    def model(
        self,
        record: LogRecord,
        event: 'ModelEvent',
        modifications: List['ModelValueModification'],
        data: Dict[str, Any],
    ) -> None:
        """
        This is for model specific logging events.
        Compiles the information into an event and saves that event
        and all modifications done.

        :param event:
        :param modifications:
        :param record:
        :param data:
        :return:
        """
        self.prepare_save(event).save()

        for modification in modifications:
            modification.event = event
            self.prepare_save(modification).save()

    def m2m(self, record: LogRecord, data: Dict[str, Any]) -> None:
        from automated_logging.signals import create_meta

        instance = data['instance']
        create_meta(instance)

        has_event = hasattr(instance._meta.dal, 'event')

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
            return self.model(record, record.event, record.modifications, record.data)
        elif record.action == 'model[m2m]':
            return self.m2m(record, record.data)
        elif record.action == 'request':
            return self.request(record, record.event)
