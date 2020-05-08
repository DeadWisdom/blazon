"""
  A Schematic is like a dataclass, but works with the rest of Blazon. This means you can create
  schemas with a familiar Python class system.
"""

import inspect
from dataclasses import dataclass
from typing import Dict, Type, Union, Any
from abc import ABC
from .schema import Schema, Undefined
from .environment import native


class Field:
    def __init__(
        self, schema=None, default=Undefined, default_factory=Undefined, type=Undefined, **kwargs
    ):
        self.value = schema or {}
        if default is not Undefined:
            self.value["default"] = default
        if default_factory is not Undefined:
            self.value["default_factory"] = default_factory
        if type is not Undefined:
            if isinstance(type, list):
                self.value['type'] = {'type': list, 'items': type[0]}
            else:
                self.value["type"] = type
        self.value.update(kwargs)

    def get_schema(self, env):
        schema = env.schema(self.value)
        return schema.value


def field(**kwargs):
    return Field(kwargs)


Schematic = None


class SchematicType(type):
    def __new__(cls, name, bases, namespace):
        new_cls = type.__new__(cls, name, bases, namespace)
        if Schematic is not None:
            new_cls.__schema__ = build_schema(new_cls, namespace.get("__schema__"))
            new_cls.__schema_fields__ = build_fields(new_cls)
        return new_cls


# pylint: disable-msg=E0102
class Schematic(metaclass=SchematicType):
    """
    Gather fields.
    Enforce type on set
    Validate function
    """

    __schema__: Schema = None
    __schema_fields__: Dict[str, "Field"]

    def __init__(self, __value__=Undefined, **kwargs):
        super().__init__()
        value = {}
        if self.__schema__:
            value.update(self.__schema__.get("default", {}))
        if __value__:
            value.update(__value__)
        value.update(kwargs)
        for k in kwargs.keys():
            if k not in self.__schema__.get("entries", {}):
                raise AttributeError(f"Unknown attribute: {k!r}")
        self.set_value(value)
        self.__post_init__()

    def __post_init__(self):
        ...

    def set_value(self, value, partial=True):
        self.__dict__.clear()
        self.__dict__.update(self.__schema__(value, partial=partial))

    def get_value(self):
        return self.__schema__(self.__dict__)

    def validate(self, partial=False):
        return self.__schema__.validate(self.__dict__, partial=partial)

    def __setattr__(self, k, v):
        self.__dict__.update(self.__schema__({k: v}, partial=True))


def build_fields(cls):
    schema = cls.__schema__
    entries = schema.get("entries", None)
    if not entries:
        return {}

    required = schema.get("required", None) or ()

    fields = {}
    for k, v in entries.items():
        if v.get("default", Undefined) is not Undefined:
            setattr(cls, k, v["default"])
        fields[k] = v  # Field(name=k, required=k in required, schema=v)

    return fields


def schema_name_from_class(cls):
    return inspect.getmodule(cls).__name__.split(".", 1)[0] + "." + cls.__name__


def build_schema(cls, value):
    if isinstance(value, Schema):
        if not value.name:
            value = value.copy(name=schema_name_from_class(cls))
        return value

    value = value or {}
    env = value.get("env", None)
    name = value.get("name", schema_name_from_class(cls))

    ### Inherited ###
    for base in cls.__bases__:
        if getattr(base, "__schema__", None):
            schema = base.__schema__
            value = dict(
                schema.value, **value
            )  # Merge parent schema with this one.  TODO: make better
            env = env or schema.env

    env = env or native

    ### Annotations ###
    entries = value.get("entries", {})
    for k, annotation in cls.__annotations__.items():
        if isinstance(annotation, list):
            entries[k] = {'type': list, 'items': {'type': annotation[0]}}
        else:
            entries[k] = {"type": annotation}
        v = getattr(cls, k, Undefined)
        if v is not Undefined:
            if isinstance(v, Field):
                entries[k] = v.get_schema(env)
            else:
                entries[k]["default"] = v

    if entries:
        value["entries"] = entries

    ### Required ###
    required = []
    for k, v in entries.items():
        if "default" not in v:
            required.append(k)

    if required:
        value["required"] = required

    return env.schema(name=name, value=value)



class OLDSchematic:  # pylint: disable-msg=E0102
    """
    Construct that carries a schema (`__schema__`) and enforces its properties
    to follow it.
    """

    __schema__ = None
    __fields__ = []

    def __init__(self, __value__=None, **kwargs):
        super().__init__()
        value = {}
        if self.__schema__:
            value.update(self.__schema__.value.get("default", {}))
        if __value__:
            value.update(__value__)
        value.update(kwargs)
        self.update_schema_value(value)

    def __repr__(self):
        value = self.get_schema_value()
        return f"{self.__class__.__name__}({value!r})"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def validate(self, partial=False):
        return self.__schema__.validate(self.__dict__, partial=partial)

    def get_schema(self):
        return self.__schema__

    def get_schema_value(self, ignore_default=False, ignore_empty=True, ignore_internal=False):
        """
        Combines the schema-property values of this object with the inherited ones,
        and returns it as a dict.

        If `ignore_default` is `True` (default) properties with default values won't
        be included.
        """
        value = {}
        fields = self.__class__.__fields__
        for k, field in fields.items():
            if ignore_internal:
                if field.config.get("internal") == False:
                    continue
            if field.has_value(self):
                try:
                    v = getattr(self, k)
                except AttributeError:
                    continue
            elif not ignore_default:
                try:
                    v = getattr(self, k)
                except AttributeError:
                    continue
            else:
                continue
            if v or ignore_empty is False:
                value[k] = v
        return value

    def update_schema_value(self, value, only_empty=False):
        for k, field in self.__class__.__fields__.items():
            if k in value:
                if not only_empty or field.has_value(self):
                    setattr(self, k, value[k])

    def marshal_as(self, system, ignore_internal=True, ignore_empty=True):
        if system is not "json":
            raise NotImplementedError(
                "Marshalling is kinda fake right now, so we can only marshal to json"
            )
        value = self.get_schema_value(ignore_internal=ignore_internal, ignore_empty=ignore_empty)
        try:
            value = marshal_to_json(value)
        except Exception as e:
            print("Marshalling failed", self)
            raise
        return value

    @classmethod
    def get_field(cls, k, default=None):
        return self.__class__.__fields__.get(k, default)

    @classmethod
    def has_field(cls, k):
        return cls.get_field(k) is not None
