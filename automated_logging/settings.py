import re
from collections import namedtuple
from logging import INFO, NOTSET, CRITICAL
from typing import NamedTuple

from django.conf import settings as st
from marshmallow import Schema, post_load, EXCLUDE
from marshmallow.fields import Boolean, String, List, Nested, Integer
from marshmallow.validate import OneOf, Range


Search = NamedTuple('Search', (('type', str), ('value', str)))


class LowerCaseString(String):
    """
    String that is always going to be serialized to a lowercase string,
    using `str.lower()`
    """

    def _deserialize(self, value, attr, data, **kwargs) -> str:
        output = super()._deserialize(value, attr, data, **kwargs)

        return output.lower()


# ModelString
# FieldString
# ApplicationString
class SearchString(String):
    """
    SearchStrings are used for models, fields and applications.
    They can be either a glob (prefixed with either glob or gl),
    regex (prefixed with either regex or re)
    or plain (prefixed with plain or pl).

    format: <prefix>:<value>
    examples:
        - gl:app*       (glob matching)
        - glob:app*     (glob matching)
        - pl:app        (exact matching)
        - plain:app     (exact matching)
        - re:^app.*$    (regex matching)
        - regex:^app.*$ (regex matching)
        - :app*         (glob matching)
        - app           (glob matching)
    """

    def _deserialize(self, value, attr, data, **kwargs) -> Search:
        output = super()._deserialize(value, attr, data, **kwargs)

        match = re.match(r'^(\w*):(.*)$', output)
        if match:
            module = match.groups()[0]
            match = match.groups()[1]

            if module.startswith('gl'):
                return Search('glob', match)
            elif module.startswith('pl'):
                return Search('plain', match)
            elif module.startswith('re'):
                return Search('regex', match)

        return Search('glob', output)


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
    applications = List(SearchString(), missing=[])

    methods = List(LowerCaseString(), missing=['GET'])
    status = List(Integer(validate=Range(min=0)), missing=[200])


class RequestDataSchema(BaseSchema):
    """
    Configuration schema for request data that is only used in RequestSchema
    and is used to enable data collection, ignore keys that are going to be omitted
    mask keys (their value is going to be replaced with <REDACTED>)
    """

    enabled = List(
        LowerCaseString(validate=OneOf(['request', 'response'])), missing=[],
    )
    query = Boolean(missing=False)

    ignore = List(LowerCaseString(), missing=[])
    mask = List(LowerCaseString(), missing=['password'])

    # TODO: add more, change name?
    content_types = List(
        LowerCaseString(validate=OneOf(['application/json'])),
        missing=['application/json'],
    )


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
    fields = List(SearchString(), missing=[])
    models = List(SearchString(), missing=[])
    applications = List(
        SearchString(),
        missing=[
            Search('plain', 'session'),
            Search('plain', 'automated_logging'),
            Search('plain', 'admin'),
            Search('plain', 'basehttp'),
            Search('plain', 'migrations'),
            Search('plain', 'contenttypes'),
        ],
    )


class ModelSchema(BaseSchema):
    """
    Configuration schema for the model module. mask property indicates
    which fields to specifically replace with <REDACTED>,
    this should be used for fields that are
    sensitive, but shouldn't be completely excluded.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(ModelExcludeSchema)

    mask = List(LowerCaseString(), missing=[])
    user_mirror = Boolean(default=False)  # maybe, name not good

    # should the log message include all modifications done?
    detailed_message = Boolean(default=True)

    # if execution_time should be measured of ModelEvent
    performance = Boolean(default=False)


class UnspecifiedExcludeSchema(BaseSchema):
    """
    Configuration schema, that is only used in UnspecifiedSchema and defines
    the configuration settings to allow unknown sources, exclude files and
    specific Django applications
    """

    unknown = Boolean(missing=False)
    files = List(LowerCaseString(), missing=[])
    applications = List(SearchString(), missing=[])


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

    modules = List(
        LowerCaseString(validate=OneOf(['request', 'model', 'unspecified'])),
        missing=['request', 'model', 'unspecified'],
    )

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
