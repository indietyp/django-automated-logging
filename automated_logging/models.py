from django.conf import settings
import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Application(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ModelStorage(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Field(BaseModel):
    name = models.CharField(max_length=255)
    model = models.ForeignKey(ModelStorage, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{} - {}'.format(self.name, self.model)


class ModelObject(BaseModel):
    value = models.CharField(max_length=255, null=True)
    field = models.ForeignKey(Field, null=True, on_delete=models.CASCADE)
    type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name='atl_modelobject_application')

    def __str__(self):
        output = '{}'.format(self.value)

        if self.field is not None:
            output += " of field {}".format(self.field)

        if self.type is not None:
            output += " in model {}.{}".format(self.type.app_label, self.type.model)

        return output


class ModelModification(BaseModel):
    previously = models.ManyToManyField(ModelObject, related_name='changelog_previous')
    currently = models.ManyToManyField(ModelObject, related_name='changelog_current')

    def __str__(self):
        print([str(v) for v in self.previously.all()])
        return ' {0} changed to {1}; '.format(", ".join(str(v) for v in self.previously.all()),
                                              ", ".join(str(v) for v in self.currently.all()))


class ModelChangelog(BaseModel):
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
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)

    url = models.URLField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{2} - {0} performed request at {3} ({1})'.format(self.user, self.created_at, self.url, self.application)

    class Meta:
        verbose_name = "Request"
        verbose_name_plural = "Requests"


class Unspecified(BaseModel):
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

        return '{} - {} - {} ({} - {})'.format(self.created_at, level, self.message, self.path, self.line)

    class Meta:
        verbose_name = "Non DJL Message"
        verbose_name_plural = "Non DJL Messages"


class LDAP(BaseModel):

    class Meta:
        verbose_name = "LDAP event log entry"
        verbose_name_plural = "LDAP event log entries"

    action = models.TextField()
    succeeded = models.NullBooleanField(blank=True, null=True)
    errorMessage = models.TextField(blank=True, null=True)

    basedn = models.TextField(blank=True, null=True)
    entry = models.TextField(blank=True, null=True)

    objectClass = models.TextField(blank=True, null=True)
    cn = models.TextField(blank=True, null=True)

    existing_members = models.TextField(blank=True, null=True)
    data_members = models.TextField(blank=True, null=True)
    diff_members = models.TextField(blank=True, null=True)


# from .signals import request, database, m2m
