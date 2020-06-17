"""Database table definitions for the application, everything is logging related."""
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import (
    CharField,
    ForeignKey,
    CASCADE,
    TextField,
    SmallIntegerField,
    PositiveIntegerField,
    SET_NULL,
)
from picklefield.fields import PickledObjectField


class BaseModel(models.Model):
    """BaseModel that is inherited from every model. Includes basic information."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Application(BaseModel):
    """
    Used to save from which application an event or model originates.
    This is used to group by application.
    """

    name = CharField(max_length=255)

    class Meta:
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    class AutomatedLogging:
        ignore = True


class ModelMirror(BaseModel):
    """
    Used to mirror properties of models - this is used to preserve logs of
    models removed to make the logs independent of the presence of the model
    in the application.
    """

    name = CharField(max_length=255)
    application = ForeignKey(Application, on_delete=CASCADE)

    class Meta:
        verbose_name = "Model Mirror"
        verbose_name_plural = "Model Mirrors"

    class AutomatedLogging:
        ignore = True


class ModelField(BaseModel):
    """
    Used to mirror properties of model fields - this is used to preserve logs of
    models and fields that might be removed/modified and have them independent
    of the actual field.
    """

    name = CharField(max_length=255)

    model = ForeignKey(ModelMirror, on_delete=CASCADE)
    type = CharField(max_length=255)  # string of type
    content_type = ForeignKey(
        ContentType, on_delete=SET_NULL, related_name='al_field', null=True
    )  # TODO: consider remove

    class Meta:
        verbose_name = "Model Field"
        verbose_name_plural = "Model Fields"

    class AutomatedLogging:
        ignore = True


class ModelEntry(BaseModel):
    """
    Used to mirror the evaluated model value (via repr) and primary key and
    to ensure the log integrity independent of presence of the entry.
    """

    model = ForeignKey(ModelMirror, on_delete=CASCADE)

    value = TextField()  # (repr)
    primary_key = TextField()

    class Meta:
        verbose_name = "Model Entry"
        verbose_name_plural = "Model Entries"

    class AutomatedLogging:
        ignore = True


class ModelEvent(BaseModel):
    """
    Used to record model entry events, like modification, removal or adding of
    values or relationships.
    """

    user = ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE
    )  # maybe don't cascade?
    model = ForeignKey(ModelEntry, on_delete=CASCADE)

    # modifications = None  # One2Many -> ModelModification
    # relationships = None  # One2Many -> ModelRelationship

    message = TextField()

    # v experimental, that is opt-in (pickled object)
    snapshot = PickledObjectField(null=True)
    execution_time = PositiveIntegerField(null=True)

    class Meta:
        verbose_name = "Model Entry Event"
        verbose_name_plural = "Model Entry Events"

    class AutomatedLogging:
        ignore = True


class ModelValueModification(BaseModel):
    """
    Used to record the model entry event modifications of simple values.

    The operation attribute can have 4 valid values:
    -1 (delete), 0 (modify), 1 (create), None (n/a)

    previous and current record the value change that happened.
    """

    operation = SmallIntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)], null=True
    )

    field = ForeignKey(ModelField, on_delete=CASCADE)

    previous = TextField(null=True)
    current = TextField(null=True)

    event = ForeignKey(ModelEvent, on_delete=CASCADE, related_name='modifications')

    class Meta:
        verbose_name = "Model Entry Event Value Modification"
        verbose_name_plural = "Model Entry Event Value Modifications"

    class AutomatedLogging:
        ignore = True


class ModelRelationshipModification(BaseModel):
    """
    Used to record the model entry even modifications of relationships. (M2M, Foreign)


    The operation attribute can have 4 valid values:
    -1 (delete), 0 (modify), 1 (create), None (n/a)

    field is the field where the relationship changed (entry got added or removed)
    and model is the entry that got removed/added from the relationship.
    """

    operation = SmallIntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)], null=True
    )

    field = ForeignKey(ModelField, on_delete=CASCADE)
    model = ForeignKey(ModelEntry, on_delete=CASCADE)

    event = ForeignKey(ModelEvent, on_delete=CASCADE, related_name='relationships')

    class Meta:
        verbose_name = "Model Entry Event Relationship Modification"
        verbose_name_plural = "Model Entry Event Relationship Modifications"

    class AutomatedLogging:
        ignore = True


class RequestContext(BaseModel):
    """
    Used to record contents of request and responses and their type.
    """

    content = PickledObjectField(null=True)
    type = CharField(max_length=255)


class RequestEvent(BaseModel):
    """
    Used to record events of requests that happened.

    uri is the accessed path and data is the data that was being transmitted
    and is opt-in for collection.

    status and method are their respective HTTP equivalents.
    """

    user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)

    uri = TextField()

    request = ForeignKey(RequestContext, on_delete=CASCADE, null=True)
    response = ForeignKey(RequestContext, on_delete=CASCADE, null=True)

    status = PositiveIntegerField()
    method = CharField(max_length=255)

    application = ForeignKey(Application, on_delete=CASCADE)

    class Meta:
        verbose_name = "Request Event"
        verbose_name_plural = "Request Events"

    class AutomatedLogging:
        ignore = True


class UnspecifiedEvent(BaseModel):
    """
    Used to record unspecified internal events that are dispatched via
    the python logging library. saves the message, level, line, file and application.
    """

    message = TextField()
    level = PositiveIntegerField()

    line = PositiveIntegerField()
    file = TextField()

    application = ForeignKey(Application, on_delete=CASCADE)

    class Meta:
        verbose_name = "Unspecified Event"
        verbose_name_plural = "Unspecified Events5"

    class AutomatedLogging:
        ignore = True
