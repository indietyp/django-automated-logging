"""
Serialization of AUTOMATED_LOGGING_SETTINGS
"""

import re
from collections import namedtuple
from functools import lru_cache
from logging import INFO, NOTSET, CRITICAL
from typing import NamedTuple

import typing
from marshmallow import Schema, post_load, EXCLUDE
from marshmallow.fields import Boolean, String, List, Nested, Integer
from marshmallow.validate import OneOf, Range

Search = NamedTuple('Search', (('type', str), ('value', str)))
Search._serialize = lambda self: f'{self.type}:{self.value}'


class Set(List):
    """
    This is like a list, just compiles down to a set when serializing.
    """

    def _serialize(
        self, value, attr, obj, **kwargs
    ) -> typing.Optional[typing.Set[typing.Any]]:
        return set(super(Set, self)._serialize(value, attr, obj, **kwargs))

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Set[typing.Any]:
        return set(super(Set, self)._deserialize(value, attr, data, **kwargs))


class LowerCaseString(String):
    """
    String that is always going to be serialized to a lowercase string,
    using `str.lower()`
    """

    def _deserialize(self, value, attr, data, **kwargs) -> str:
        output = super()._deserialize(value, attr, data, **kwargs)

        return output.lower()


class SearchString(String):
    """
    Used for:
    - ModelString
    - FieldString
    - ApplicationString
    - FileString

    SearchStrings are used for models, fields and applications.
    They can be either a glob (prefixed with either glob or gl),
    regex (prefixed with either regex or re)
    or plain (prefixed with plain or pl).

    All SearchStrings ignore the case of the raw string.

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
        if isinstance(value, dict) and 'type' in value and 'value' in value:
            value = f'{value["type"]}:{value["value"]}'

        output = super()._deserialize(value, attr, data, **kwargs)

        match = re.match(r'^(\w*):(.*)$', output, re.IGNORECASE)
        if match:
            module = match.groups()[0].lower()
            match = match.groups()[1]

            if module.startswith('gl'):
                return Search('glob', match.lower())
            elif module.startswith('pl'):
                return Search('plain', match.lower())
            elif module.startswith('re'):
                # regex shouldn't be lowercase
                # we just ignore the case =
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

    @staticmethod
    def namedtuple_or(left: NamedTuple, right: NamedTuple):
        """
        __or__ implementation for the namedtuple
        """
        values = {}

        if not isinstance(left, tuple) or not isinstance(right, tuple):
            raise NotImplemented

        for name in left._fields:
            field = getattr(left, name)
            values[name] = field

            if not hasattr(right, name):
                continue

            if isinstance(field, tuple) or isinstance(field, set):
                values[name] = field | getattr(right, name)

        return left._replace(**values)

    @staticmethod
    def namedtuple_factory(name, keys):
        """
        create the namedtuple from the name and keys to attach functions that are needed.

        Attaches:
            binary **or** operation to support globals propagation
        """
        Object = namedtuple(name, keys)
        Object.__or__ = BaseSchema.namedtuple_or
        return Object

    @post_load
    def make_namedtuple(self, data: typing.Dict, **kwargs):
        """
        converts the loaded data dict into a namedtuple

        :param data: loaded data
        :param kwargs: marshmallow kwargs
        :return: namedtuple
        """
        name = self.__class__.__name__.replace('Schema', '')

        Object = BaseSchema.namedtuple_factory(name, data.keys())
        return Object(**data)


class RequestExcludeSchema(BaseSchema):
    """
    Configuration schema for request exclusion, that is only used in RequestSchema,
    is used to exclude unknown sources, applications, methods and status codes.
    """

    unknown = Boolean(missing=False)
    applications = Set(SearchString(), missing=set())

    methods = Set(LowerCaseString(), missing={'GET'})
    status = Set(Integer(validate=Range(min=0)), missing={200})


class RequestDataSchema(BaseSchema):
    """
    Configuration schema for request data that is only used in RequestSchema
    and is used to enable data collection, ignore keys that are going to be omitted
    mask keys (their value is going to be replaced with <REDACTED>)
    """

    enabled = Set(
        LowerCaseString(validate=OneOf(['request', 'response'])), missing=set(),
    )
    query = Boolean(missing=False)

    ignore = Set(LowerCaseString(), missing=set())
    mask = Set(LowerCaseString(), missing={'password'})

    # TODO: add more, change name?
    content_types = Set(
        LowerCaseString(validate=OneOf(['application/json'])),
        missing={'application/json'},
    )


class RequestSchema(BaseSchema):
    """
    Configuration schema for the request module.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(RequestExcludeSchema)

    data = MissingNested(RequestDataSchema)

    ip = Boolean(missing=True)
    # TODO: performance setting?


class ModelExcludeSchema(BaseSchema):
    """
    Configuration schema, that is only used in ModelSchema and is used to
    exclude unknown sources, fields, models and applications.

    fields should be either <field> (every field that matches this name will be excluded),
    or <model>.<field>, or <application>.<model>.<field>

    models should be either <model> (every model regardless of module or application).
    <module> (python module location) or <module>.<model> (python module location)
    """

    unknown = Boolean(missing=False)
    fields = Set(SearchString(), missing=set())
    models = Set(SearchString(), missing=set())
    applications = Set(SearchString(), missing=set())


class ModelSchema(BaseSchema):
    """
    Configuration schema for the model module. mask property indicates
    which fields to specifically replace with <REDACTED>,
    this should be used for fields that are
    sensitive, but shouldn't be completely excluded.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(ModelExcludeSchema)

    mask = Set(LowerCaseString(), missing=set())
    user_mirror = Boolean(missing=False)  # maybe, name not good

    # should the log message include all modifications done?
    detailed_message = Boolean(missing=True)

    # if execution_time should be measured of ModelEvent
    performance = Boolean(missing=False)
    snapshot = Boolean(missing=False)


class UnspecifiedExcludeSchema(BaseSchema):
    """
    Configuration schema, that is only used in UnspecifiedSchema and defines
    the configuration settings to allow unknown sources, exclude files and
    specific Django applications
    """

    unknown = Boolean(missing=False)
    files = Set(SearchString(), missing=set())
    applications = Set(SearchString(), missing=set())


class UnspecifiedSchema(BaseSchema):
    """
    Configuration schema for the unspecified module.
    """

    loglevel = Integer(missing=INFO, validate=Range(min=NOTSET, max=CRITICAL))
    exclude = MissingNested(UnspecifiedExcludeSchema)


class GlobalsExcludeSchema(BaseSchema):
    """
    Configuration schema, that is used for every single module.
    There are some packages where it is sensible to have the same
    exclusions.

    Things specified in globals will get appended to the other configurations.
    """

    applications = Set(
        SearchString(),
        missing={
            Search('glob', 'session*'),
            Search('plain', 'admin'),
            Search('plain', 'basehttp'),
            Search('plain', 'migrations'),
            Search('plain', 'contenttypes'),
        },
    )


class GlobalsSchema(BaseSchema):
    """
    Configuration schema for global, module unspecific configuration details.
    """

    exclude = MissingNested(GlobalsExcludeSchema)


class ConfigSchema(BaseSchema):
    """
    Skeleton configuration schema, that is used to enable/disable modules
    and includes the nested module configurations.
    """

    modules = Set(
        LowerCaseString(validate=OneOf(['request', 'model', 'unspecified'])),
        missing={'request', 'model', 'unspecified'},
    )

    request = MissingNested(RequestSchema)
    model = MissingNested(ModelSchema)
    unspecified = MissingNested(UnspecifiedSchema)

    globals = MissingNested(GlobalsSchema)


default: namedtuple = ConfigSchema().load({})


class Settings:
    """
    Settings wrapper,
    with the wrapper we can force lru_cache to be
    cleared on the specific instance
    """

    def __init__(self):
        self.loaded = None
        self.load()

    @lru_cache
    def load(self):
        """
        loads settings from the schemes provided,
        done via function to utilize LRU cache
        """

        from django.conf import settings as st

        loaded: namedtuple = default

        if hasattr(st, 'AUTOMATED_LOGGING'):
            loaded = ConfigSchema().load(st.AUTOMATED_LOGGING)

        # be sure `loaded` has globals as we're working with those,
        # if that is not the case early return.
        if not hasattr(loaded, 'globals'):
            return loaded

        # use the binary **or** operator to apply globals to Set() attributes
        values = {}
        for name in loaded._fields:
            field = getattr(loaded, name)
            values[name] = field

            if not isinstance(field, tuple) or name == 'globals':
                continue

            values[name] = field | loaded.globals

        self.loaded = loaded._replace(**values)
        return self

    def __getattr__(self, item):
        # self.load() should only trigger when the cache is invalid
        self.load()

        return getattr(self.loaded, item)


@lru_cache
def load_dev():
    """
    utilize LRU cache and local imports to always
    have an up to date version of the settings

    :return:
    """
    from django.conf import settings as st

    return getattr(st, 'AUTOMATED_LOGGING_DEV', False)


settings = Settings()
dev = load_dev()
