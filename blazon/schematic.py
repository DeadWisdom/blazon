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
        self,
        schema=None,
        default=Undefined,
        default_factory=Undefined,
        type=Undefined,
        repr=False,
        **kwargs,
    ):
        self.repr = repr
        self.value = schema or {}
        if default is not Undefined:
            self.value["default"] = default
        if default_factory is not Undefined:
            self.value["default_factory"] = default_factory
        if type is not Undefined:
            if isinstance(type, list):
                self.value["type"] = {"type": list, "items": type[0]}
            else:
                self.value["type"] = type
        self.value.update(kwargs)

    def get_schema(self, env):
        schema = env.schema(self.value)
        return schema.value


def field(**kwargs):
    return Field(**kwargs)


Schematic = None


class SchematicType(type):
    def __new__(cls, name, bases, namespace):
        new_cls = type.__new__(cls, name, bases, namespace)
        if Schematic is not None:
            new_cls.__schema__ = build_schema(new_cls, namespace.get("__schema__"))
            if new_cls.__schema__:
                new_cls.__schema_fields__ = build_fields(new_cls)
                new_cls.__schema__.env.schematics[name] = new_cls
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

    def __repr__(self):
        parts = []
        for attr in self.__schema__.get("__repr__", []):
            value = getattr(self, attr, Undefined)
            if value is Undefined:
                continue
            parts.append(f"{attr}={value!r}")
        if parts:
            values = ", ".join(parts)
            return f"{self.__class__.__name__}({values})"
        else:
            return f"<{self.__class__.__name__}>"

    def __post_init__(self):
        ...

    def set_value(self, value, partial=True):
        self.__dict__.clear()
        self.__dict__.update(self.__schema__(value, partial=partial))

    def get_value(self, partial=True):
        return self.__schema__(self.__dict__, partial=partial)

    def validate(self, partial=False):
        return self.__schema__.validate(self.__dict__, partial=partial)

    def __setattr__(self, k, v):
        self.__dict__.update(self.__schema__({k: v}, partial=True))


def build_fields(cls):
    schema = cls.__schema__
    if not schema:
        return {}

    entries = schema.get("entries", None)
    if not entries:
        return {}

    fields = {}
    for k, v in entries.items():
        if v.get("default", Undefined) is not Undefined:
            setattr(cls, k, v["default"])
        fields[k] = v
        if isinstance(v, dict) and "$ref" in v:
            setattr(cls, k, RefDescriptor(k, v["$ref"].rsplit("/", 1)[-1]))

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
    repr = []
    for k, annotation in cls.__annotations__.items():
        if k.startswith("__"):
            continue
        if isinstance(annotation, list):
            entries[k] = {"type": list, "items": {"type": annotation[0]}}
        else:
            entries[k] = {"type": annotation}
        v = getattr(cls, k, Undefined)
        if v is Undefined:
            continue
        if isinstance(v, Field):
            entries[k] = v.get_schema(env)
            if v.repr:
                repr.append(k)
        else:
            entries[k]["default"] = v

    if entries:
        value["entries"] = entries

    if repr:
        value["__repr__"] = sorted(repr)

    ### Required ###
    required = []
    for k, v in entries.items():
        if "default" not in v:
            required.append(k)

    if required:
        value["required"] = sorted(required)

    if not value:
        return None

    return env.schema(name=name, value=value)


class RefDescriptor:
    def __init__(self, attribute_name, schema_name):
        self.attribute_name = attribute_name
        self.schema_name = schema_name

    def __get__(self, obj, type=None) -> Any:
        value = obj.__dict__.get(self.attribute_name, Undefined)
        if value is Undefined:
            raise AttributeError(self.attribute_name)
        schematic = obj.__schema__.env.schematics.get(self.schema_name)
        if not schematic:
            return value
        if isinstance(value, schematic):
            return value
        return schematic(value)

    def __set__(self, obj, value) -> None:
        obj.__dict__.update(obj.__schema__({self.attribute_name: value}, partial=True))

    def __delete__(self, obj) -> None:
        del obj.__dict__[self.attribute_name]
