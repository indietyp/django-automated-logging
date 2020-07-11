import re
from datetime import timedelta
from logging import Handler, LogRecord
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING, List, Optional, Union


from django.utils import timezone
from django.db.models import ForeignObject, Model
from django.db.models.fields.reverse_related import ForeignObjectRel

if TYPE_CHECKING:
    # we need to do this, to avoid circular imports
    from automated_logging.models import (
        RequestEvent,
        ModelEvent,
        ModelValueModification,
        ModelRelationshipModification,
    )


class DatabaseHandler(Handler):
    def __init__(
        self,
        *args,
        max_age: Optional[Union[int, str, timedelta]] = None,
        batch: Optional[int] = 1,
        **kwargs
    ):
        if 'maxage' in kwargs and not max_age:
            max_age = kwargs['maxage']

        self.limit = batch or 1
        self.instances = []
        self.max_age = self._convert_max_age(max_age) if max_age else None
        super(DatabaseHandler, self).__init__(*args, **kwargs)

    @staticmethod
    def _convert_max_age(target: Union[int, str, timedelta]) -> Optional[timedelta]:
        if isinstance(target, timedelta):
            return target

        if isinstance(target, int):
            return timedelta(seconds=target)

        if isinstance(target, str):
            REGEX = (
                r'^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$'
            )
            match = re.match(REGEX, target, re.IGNORECASE)
            if not match:
                return None

            components = list(match.groups())
            # remove leading T capture - isn't used, by removing the 5th capture group
            components.pop(4)

            adjusted = {'days': 0, 'seconds': 0}
            conversion = [
                ['days', 365],  # year
                ['days', 30],  # month
                ['days', 7],  # week
                ['days', 1],  # day
                ['seconds', 3600],  # hour
                ['seconds', 60],  # minute
                ['seconds', 1],  # second
            ]

            for pointer in range(len(components)):
                if not components[pointer]:
                    continue
                rate = conversion[pointer]
                native = int(re.findall(r'(\d+)', components[pointer])[0])

                adjusted[rate[0]] += native * rate[1]

            return timedelta(**adjusted)

    def save(self, instance):
        """
        Internal save procedure.
        Handles deletion when an event exceeds max_age
        and batch saving via atomic transactions.

        :return: None
        """
        from django.db import transaction
        from automated_logging.models import ModelEvent, RequestEvent, UnspecifiedEvent

        self.instances.append(instance)
        if len(self.instances) < self.limit:
            return

        with transaction.atomic():
            [i.save() for i in self.instances]
            self.instances.clear()

            for Event in [ModelEvent, RequestEvent, UnspecifiedEvent]:
                Event.objects.filter(
                    created_at__lte=timezone.now() - self.max_age
                ).delete()

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
        """
        This is for messages that are not sent from django-automated-logging.
        The option to still save these log messages is there. We create
        the event in the handler and then save them.

        :param record:
        :return:
        """
        from automated_logging.models import UnspecifiedEvent, Application
        from django.apps import apps

        event = UnspecifiedEvent()
        if hasattr(record, 'message'):
            event.message = record.message
        event.level = record.levelno
        event.line = record.lineno
        event.file = Path(record.pathname) / Path(record.filename)

        # this is semi-reliable, but I am unsure of a better way to do this.
        applications = apps.app_configs.keys()
        path = Path(record.pathname) / Path(record.filename).stem
        candidates = [p for p in path.parts if p in applications]
        if candidates:
            # use the last candidate (closest to file)
            event.application = Application(name=candidates[-1])
        else:
            # if we cannot find the application, we use the module as application
            event.application = Application(name=record.module)

        self.prepare_save(event)
        self.save(event)

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
        self.prepare_save(event)
        self.save(event)

        for modification in modifications:
            modification.event = event
            self.prepare_save(modification)
            self.save(modification)

    def m2m(
        self,
        record: LogRecord,
        event: 'ModelEvent',
        relationships: List['ModelRelationshipModification'],
        data: Dict[str, Any],
    ) -> None:
        self.prepare_save(event)
        self.save(event)

        for relationship in relationships:
            relationship.event = event
            self.prepare_save(relationship)
            self.save(relationship)

    def request(self, record: LogRecord, event: 'RequestEvent') -> None:
        """
        The request event already has a model prepared that we just
        need to prepare and save.

        TODO: request and response context parsing, masking and removal

        :param record: LogRecord
        :param event: Event supplied via the LogRecord
        :return: nothing
        """

        self.prepare_save(event)
        self.save(event)

    def emit(self, record: LogRecord) -> None:
        """
        Emit function that gets triggered for every log message in scope.

        The record will be processed according to the action set.
        :param record:
        :return:
        """
        if not hasattr(record, 'action'):
            return self.unspecified(record)

        if record.action == 'model':
            return self.model(record, record.event, record.modifications, record.data)
        elif record.action == 'model[m2m]':
            return self.m2m(record, record.event, record.relationships, record.data)
        elif record.action == 'request':
            return self.request(record, record.event)
