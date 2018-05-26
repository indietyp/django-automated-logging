"""Database table definitions for the application, everything is logging related."""
from django.conf import settings
import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType


class BaseModel(models.Model):
    """BaseModel that is inherited from every model. Includes basic information."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Application(BaseModel):
    """
    Table for every application that might be used

    - this is not created get_or_create,
    so it is not yet a full representation of every application installed,
    this might follow
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        """Returns name of application."""
        return self.name


class Field(BaseModel):
    """
    Table definition for a regular field.

    Is tied to a ContentTypes.
    If the model will be deleted all the related fields will be therefor too.
    """

    name = models.CharField(max_length=255)
    model = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE, related_name='dal_field')

    def __str__(self):
        return '{} - {}'.format(self.name, self.model)


class ModelObject(BaseModel):
    """
    BaseObject of the system.

    BaseObject for everything logging related.
    consists of a value: gathered through repr()
    field - which is a definition of the field
    and if it refers to a relationship the model.
    """

    value = models.CharField(max_length=255, null=True)
    field = models.ForeignKey(Field, null=True, on_delete=models.CASCADE)
    type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name='atl_modelobject_application')

    def __str__(self):
        output = '{}'.format(self.value)

        if self.field is not None:
            output += " of field: {}".format(self.field.name)

        if self.type is not None:
            output += " in model: {}.{}".format(self.type.app_label, self.type.model)

        return output


class ModelModification(BaseModel):
    """Saves the two states of several fields."""

    previously = models.ManyToManyField(ModelObject, related_name='changelog_previous')
    currently = models.ManyToManyField(ModelObject, related_name='changelog_current')

    def __str__(self):
        return ' {0} changed to {1}; '.format(", ".join(str(v) for v in self.previously.all()),
                                              ", ".join(str(v) for v in self.currently.all()))


class ModelChangelog(BaseModel):
    """General changelog, saves which fields are removede, inserted (both m2m) and which are modified."""

    modification = models.OneToOneField(ModelModification, null=True, on_delete=models.CASCADE)
    inserted = models.ManyToManyField(ModelObject, related_name='changelog_inserted')
    removed = models.ManyToManyField(ModelObject, related_name='changelog_removed')

    information = models.OneToOneField(ModelObject, null=True, on_delete=models.CASCADE)

    def __str__(self):
        output = ''
        if self.modification is not None:
            output += '{0} in {1}'.format(self.modification, self.information)
        if self.inserted.count() > 0:
            output += '{0} was inserted into {1}; '.format(", ".join(str(v) for v in self.inserted.all()), self.information)
        if self.removed.count() > 0:
            output += '{0} was removed from {1}; '.format(", ".join(str(v) for v in self.removed.all()), self.information)

        return output


class Model(BaseModel):
    """This ties a changelog to a specific user, this is used by the DatabaseHandler."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='atl_model_application', null=True)

    message = models.TextField(null=True)

    MODES = (
        (0, 'n/a'),
        (1, 'add'),
        (2, 'change'),
        (3, 'delete'),
    )
    action = models.PositiveSmallIntegerField(choices=MODES, default=0)

    information = models.OneToOneField(ModelObject, on_delete=models.CASCADE, related_name='atl_model_information', null=True)
    modification = models.ForeignKey(ModelChangelog, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{0} - {1}'.format(self.created_at, self.message)

    class Meta:
        verbose_name = 'Changelog'
        verbose_name_plural = 'Changelogs'


class Request(BaseModel):
    """The model where every request is saved."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)

    uri = models.URLField()
    method = models.CharField(max_length=64)
    status = models.PositiveSmallIntegerField(null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{2} - {0} performed request at {3} ({1})'.format(self.user, self.created_at, self.uri, self.application)

    class Meta:
        verbose_name = "Request"
        verbose_name_plural = "Requests"


class Unspecified(BaseModel):
    """Logging messages that are saved by non DAL systems."""

    message = models.TextField(null=True)
    level = models.PositiveSmallIntegerField(default=20)

    file = models.CharField(max_length=255, null=True)
    line = models.PositiveIntegerField(null=True)

    def __str__(self):
        if self.level == 10:
            level = 'DEBUG'
        elif self.level == 20:
            level = 'INFO'
        elif self.level == 30:
            level = 'WARNING'
        elif self.level == 40:
            level = 'ERROR'
        elif self.level == 50:
            level = 'CRITICAL'
        else:
            level = 'NOTSET'

        return '{} - {} - {} ({} - {})'.format(self.created_at, level, self.message, self.file, self.line)

    class Meta:
        verbose_name = "Non DAL Message"
        verbose_name_plural = "Non DAL Messages"
