from django.conf import settings as st
from logging import INFO, NOTSET, CRITICAL
from collections import namedtuple
from marshmallow import Schema, post_load, EXCLUDE
from marshmallow.fields import Boolean, String, List, Nested, Integer
from marshmallow.validate import OneOf, Range


class MissingNested(Nested):
    def __init__(self, *args, **kwargs):
        if 'missing' not in kwargs:
            kwargs['missing'] = lambda: args[0]().load({})

        super().__init__(*args, **kwargs)


class BaseSchema(Schema):
    def __init__(self, *args, **kwargs):
        if 'unknown' not in kwargs:
            kwargs['unknown'] = EXCLUDE

        super().__init__(*args, **kwargs)

    @post_load
    def make_namedtuple(self, data, **kwargs):
        name = self.__class__.__name__.replace('Schema', '')

        Object = namedtuple(name, data.keys())
        return Object(**data)


class RequestExcludeSchema(BaseSchema):
    unknown = Boolean(missing=False)
    applications = List(String(), missing=[])

    methods = List(String(), missing=[])
    status = List(Integer(validate=Range(min=0)), missing=[])


class RequestDataSchema(BaseSchema):
    enabled = Boolean(missing=True)
    ignore = List(String(), missing=[])


class RequestSchema(BaseSchema):
    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(RequestExcludeSchema)

    data = MissingNested(RequestDataSchema)


class ModelExcludeSchema(BaseSchema):
    unknown = Boolean(missing=False)
    fields = List(String(), missing=[])
    models = List(String(), missing=[])
    applications = List(String(), missing=['session', 'automated_logging', 'admin',
                                           'basehttp', 'migrations', 'contenttypes'])


class ModelSchema(BaseSchema):
    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(ModelExcludeSchema)

    mask = List(String(), missing=[])


class UnspecifiedExcludeSchema(BaseSchema):
    unknown = Boolean(missing=False)
    files = List(String(), missing=[])
    applications = List(String(), missing=[])


class UnspecifiedSchema(BaseSchema):
    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(UnspecifiedExcludeSchema)


class ConfigSchema(BaseSchema):
    modules = List(String(validate=OneOf(['request', 'model', 'unspecified'])),
                   missing=['request', 'model', 'unspecified'])

    request = MissingNested(RequestSchema)
    model = MissingNested(ModelSchema)
    unspecified = MissingNested(UnspecifiedSchema)


# TODO: validate applications, models and fields, mask appropriately
default = ConfigSchema().load({})
if hasattr(st, 'AUTOMATED_LOGGING'):
    settings = ConfigSchema().load(st.AUTOMATED_LOGGING)
else:
    settings = default
