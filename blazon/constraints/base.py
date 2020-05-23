from inflection import underscore
from functools import wraps
from dataclasses import dataclass, field
from typing import Callable, Type, List, Mapping

from ..helpers import (
    Undefined,
    hashish,
    identity,
    SchemaValidationResult,
    ConstraintFailure,
    ValidationError,
    ConstraintNotApplicable,
)


@dataclass
class Constraint:
    name: str
    description: str
    compiler: Callable
    require: [Type]
    exclude: [Type]

    def __call__(self, schema, value):
        return self.compiler(schema, value)

    def is_applicable(self, i):
        if self.require is not None and not isinstance(i, self.require):
            return False
        if self.exclude is not None and isinstance(i, self.exclude):
            return False
        return True

    def is_applicable_type(self, t):
        if self.require is not None and t is not Undefined and not issubclass(t, self.require):
            return False
        if self.exclude is not None and t is not Undefined and issubclass(t, self.exclude):
            return False
        return True


### Registry ###
class ConstraintRegistry:
    def __init__(self, inflection=underscore, registry=None, aliases=None):
        self.registry = registry or {}
        self.inflection = inflection
        self.aliases = aliases or {}

    def add(
        self,
        compiler: Callable,
        name: str = None,
        description: str = None,
        require=None,
        exclude=None,
    ):
        if require:
            require = tuple(require)
        if exclude:
            exclude = tuple(exclude)

        name = self.inflection(name or compiler.__name__)
        constraint = self.registry[name] = Constraint(
            name=name, description=description, compiler=compiler, require=require, exclude=exclude
        )
        return constraint

    def get(self, name):
        return self.registry.get(self.inflection(name))

    def get_alias(self, name):
        if name in self.aliases:
            return self.aliases[name]
        return self.inflection(name)

    def clone(
        self, *, include: List[str] = None, map: Mapping[str, str] = {}, inflection=underscore
    ):
        new_registry = {}
        if include is None:
            include = self.registry.keys()
        for name in include:
            new_registry[inflection(name)] = self.registry[self.inflection(name)]
        aliases = {}
        for new_name, old_name in map.items():
            aliases[self.inflection(old_name)] = inflection(new_name)
            new_registry[inflection(new_name)] = self.registry[self.inflection(old_name)]
        return self.__class__(registry=new_registry, inflection=inflection, aliases=aliases)


### Base Constraints ###
constraints = ConstraintRegistry()


def register(description: str, name: str = None, require=None, exclude=None):
    def decorator(compiler: Callable):
        constraints.add(
            compiler=compiler, description=description, name=name, require=require, exclude=exclude
        )
        return compiler

    return decorator


### Base Types ###
@register(description="must be of type {value!r}", name="type")
def type_constraint(schema, value):
    if isinstance(value, str):
        try:
            value = schema.env.get_primitive_type(value)
        except KeyError:
            raise ValueError(
                f"Unknown primitive type, environment {schema.env!r} has no primitive: {value!r}"
            )

    if not isinstance(value, type):
        raise ValueError(f"Type constraint given a value that is not a type: {value!r}")

    def handler(instance, convert=False, partial=False):
        if isinstance(instance, value):
            return instance

        if convert:
            return value(instance)

        raise ValidationError

    # Special case for the type constructor, we also return the expected type.
    return handler, value


@register(description="must be one of: {value!r}")
def enum(schema, value):
    choices = set(value)

    def handler(instance, convert=False, partial=False):
        if instance not in choices:
            raise ValidationError
        return instance

    return handler


@register(description="must be {value!r}")
def const(schema, value):
    def handler(instance, convert=False, partial=False):
        if instance != value:
            if not convert:
                raise ValidationError
        return value

    return handler


@register(description="a default value")
def default(schema, value):
    return None


@register(description="the name of the schema")
def name(schema, value):
    return None


@register(description="a function to create a default value")
def default_factory(schema, value):
    return None


@register(description="list of fields that should show up in the default __repr__")
def __repr__(schema, value):
    return None
