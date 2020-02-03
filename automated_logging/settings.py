from collections import namedtuple
from logging import INFO, NOTSET, CRITICAL
from typing import Optional

from django.conf import settings as st
from marshmallow import Schema, post_load, EXCLUDE
from marshmallow.fields import Boolean, String, List, Nested, Integer
from marshmallow.validate import OneOf, Range


# ModelString
# FieldString
class ApplicationString(String):
    """
    TODO: parsing in application, convert strings into regex strings

    used to convert an input string into an appropriately formatted string,
    "*" is going to be evaluated to 0+ unspecified characters, r'' strings are
    going to be evaluated via the python regex module.

    allowed values:
        - application
        - app*
        - application.module
        - app*.module
        - app*.mod*
        - application.mod*
        - *cation
        - app*cation

    examples values:
        - django.*
        - *_logging
        - automated*
        - dj*.ht*
    """

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        output = super()._serialize(value, attr, obj, **kwargs)

        return output


class MissingNested(Nested):
    """
    Modified marshmallow Nested, that is defaulting missing to loading an empty
    schema, to populate it with data.
    """

    def __init__(self, *args, **kwargs):
        if 'missing' not in kwargs:
            kwargs['missing'] = lambda: args[0]().load({})

        super().__init__(*args, **kwargs)


class BaseSchema(Schema):
    """
    Modified marshmallow Schema, that is defaulting the unknown keyword to EXCLUDE,
    not RAISE (marshmallow default) and when loading converts the dict into a namedtuple.
    """

    def __init__(self, *args, **kwargs):
        if 'unknown' not in kwargs:
            kwargs['unknown'] = EXCLUDE

        super().__init__(*args, **kwargs)

    @post_load
    def make_namedtuple(self, data, **kwargs):
        """
        converts the loaded data dict into a namedtuple

        :param data: loaded data
        :param kwargs: marshmallow kwargs
        :return: namedtuple
        """
        name = self.__class__.__name__.replace('Schema', '')

        Object = namedtuple(name, data.keys())
        return Object(**data)


class RequestExcludeSchema(BaseSchema):
    """
    Configuration schema for request exclusion, that is only used in RequestSchema,
    is used to exclude unknown sources, applications, methods and status codes.
    """
    unknown = Boolean(missing=False)
    applications = List(String(), missing=[])

    methods = List(String(), missing=['GET'])
    status = List(Integer(validate=Range(min=0)), missing=[200])


class RequestDataSchema(BaseSchema):
    """
    Configuration schema for request data that is only used in RequestSchema
    and is used to enable data collection, ignore keys that are going to be omitted
    mask keys (their value is going to be replaced with <REDACTED>)
    """
    enabled = Boolean(missing=False)
    ignore = List(String(), missing=[])
    mask = List(String(), missing=['password'])


class RequestSchema(BaseSchema):
    """
    Configuration schema for the request module.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(RequestExcludeSchema)

    data = MissingNested(RequestDataSchema)


class ModelExcludeSchema(BaseSchema):
    """
    Configuration schema, that is only used in ModelSchema and is used to
    exclude unknown sources, fields, models and applications.
    """

    unknown = Boolean(missing=False)
    fields = List(String(), missing=[])
    models = List(String(), missing=[])
    applications = List(String(), missing=['session', 'automated_logging', 'admin',
                                           'basehttp', 'migrations', 'contenttypes'])


class ModelSchema(BaseSchema):
    """
    Configuration schema for the model module. mask is used to replace specific
    fields when changed with <REDACTED>, this should be used for fields that are
    sensitive, but shouldn't be completely excluded.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(ModelExcludeSchema)

    mask = List(String(), missing=[])
    user_mirror = Boolean(default=False)  # maybe, name not good


class UnspecifiedExcludeSchema(BaseSchema):
    """
    Configuration schema, that is only used in UnspecifiedSchema and defines
    the configuration settings to allow unknown sources, exclude files and
    specific Django applications
    """

    unknown = Boolean(missing=False)
    files = List(String(), missing=[])
    applications = List(String(), missing=[])


class UnspecifiedSchema(BaseSchema):
    """
    Configuration schema for the unspecified module.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(UnspecifiedExcludeSchema)


class ConfigSchema(BaseSchema):
    """
    Skeleton configuration schema, that is used to enable/disable modules
    and includes the nested module configurations.
    """

    modules = List(String(validate=OneOf(['request', 'model', 'unspecified'])),
                   missing=['request', 'model', 'unspecified'])

    request = MissingNested(RequestSchema)
    model = MissingNested(ModelSchema)
    unspecified = MissingNested(UnspecifiedSchema)


# TODO: validate applications, models and fields, mask appropriately
default: namedtuple = ConfigSchema().load({})
settings: namedtuple = default
if hasattr(st, 'AUTOMATED_LOGGING'):
    settings = ConfigSchema().load(st.AUTOMATED_LOGGING)

# model should be BaseModel, *.BaseModel, application.BaseModel

# field should be field = *.*.field, application.Model.field,
# application.*.field, application.Model.*, Model.field = *.Model.field
