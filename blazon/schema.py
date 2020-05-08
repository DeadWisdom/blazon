import sys
import hashlib
import logging
from functools import wraps
from typing import Any
from collections import OrderedDict
from shortuuid import uuid
from dataclasses import dataclass, field, replace
from .helpers import (
    Undefined,
    hashish,
    ValidationError,
    SchemaValidationResult,
    ConstraintNotApplicable,
    ConstraintFailure,
    ConstraintKeyError,
)


def wrap_applicable_checker(constraint, handler):
    @wraps(handler)
    def wrapper(instance, *a, **kw):
        if not constraint.is_applicable(instance):
            raise ConstraintNotApplicable()
        return handler(instance, *a, **kw)

    return wrapper


@dataclass(frozen=True)
class Schema:
    """
    The Schema class is the primary mechanism for doing what Blazon does. It holds the information
    needed to validate and describe data via a set of Constraints.

    Normally you won't instantiate this directly, but rather use an environment like:

        >>> import blazon
        >>> blazon.schema(...)  # Use the default native environment

        >>> from blazon import Blazon
        >>> env = Blazon()      # Create your own environment
        >>> env.schema(...)
    """

    value: dict
    env: object
    strict: bool = False
    name: str = field(default_factory=uuid)
    type: Any = field(init=False)  # This is the type given by the 'type' constraint
    constraints: dict = field(default_factory=OrderedDict, init=False)

    def __repr__(self) -> str:
        if self.name:
            return f"{self.__class__.__name__}(name={self.name!r})"
        return f"{self.__class__.__name__}({self.value!r})"

    def __hash__(self) -> int:
        if self.name:
            return hash(self.name)
        else:
            return hashish(self.value)

    def get(self, key, default=None):
        normal = self.env.constraints.get_alias(key)
        for k in self.value.keys():
            if self.env.inflection(k) == normal:
                return self.value[k]
        return default

    def compile(self) -> None:
        self.constraints.clear()

        self.__dict__["type"] = Undefined

        # Compile the type constraint first
        if "type" in self.value:
            type_constraint = self.env.get_constraint("type")
            # Special case for the type constraint, we also get back an expected type:
            self.constraints["type"], self.__dict__["type"] = type_constraint(
                self, self.value["type"]
            )

        for k, v in self.value.items():
            if k == "type":
                continue

            constraint = self.env.get_constraint(k)
            if not constraint:
                if self.strict:
                    raise ConstraintKeyError(k)
                continue

            try:
                if not constraint.is_applicable_type(self.type):
                    raise ConstraintNotApplicable()

                handler = constraint(self, v)
                if handler is None:
                    continue
            except ConstraintNotApplicable:
                if self.strict:
                    raise

            if self.type is Undefined:
                handler = wrap_applicable_checker(constraint, handler)

            self.constraints[k] = handler

    def copy(self, **changes) -> "Schema":
        clone = replace(self, **changes)
        clone.compile()
        return clone

    def validate(self, instance: Any, partial: bool = False) -> SchemaValidationResult:
        results = {}

        for name, c in self.constraints.items():
            try:
                c(instance, convert=False, partial=partial)
            except ValueError as err:
                results[c] = err
                if name == "type":
                    break
            except ConstraintNotApplicable as err:
                if self.strict:
                    results[c] = err

        return SchemaValidationResult(self, instance, results)

    def __call__(self, instance: Any, partial: bool = False) -> "Schema":  # WOW, FUCK, plugin?
        for name, c in self.constraints.items():
            try:
                instance = c(instance, convert=True, partial=partial)
            except ConstraintNotApplicable:
                if self.strict:
                    raise ConstraintFailure(
                        "constraint not applicable to type", c, sub_errors=[err], path=[name],
                    ).with_traceback(tb)
            except (ValueError, AssertionError) as err:
                tb = sys.exc_info()[2]
                err = ConstraintFailure(c, sub_errors=[err], path=[name],).with_traceback(tb)
                raise err
            except ConstraintFailure as e:
                e.schema = self
                e.path.insert(0, name)
                raise

        return instance
