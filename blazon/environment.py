import logging, warnings
from dataclasses import dataclass, field
from typing import Dict, Callable, Type, Union
from datetime import date, datetime, time
from collections.abc import Mapping, MutableMapping, Sequence, Callable
from numbers import Number
from decimal import Decimal
from inflection import underscore

from .helpers import (
    ValidationError,
    Undefined,
    SchemaValidationResult,
    ConstraintKeyError,
)
from .schema import Schema
from .constraints import constraints, ConstraintRegistry


@dataclass  # We can't use Blazon for Blazon, unfortunately. It'd be a lot cooler if you did.
class Environment:
    __hash__ = None

    name: str
    inflection: Callable = field(default=underscore, repr=False)
    schemas: Dict[str, Schema] = field(default_factory=dict, repr=False)
    strict: bool = True  # If strict is true, we will raise errors when constraints cannot be found.
    ignore_formats: bool = field(default=False, repr=False)  # Ignore 'format' constraint
    ignore_these_formats: set = field(default_factory=set, repr=False)  # Ignore the given formats.
    constraints: ConstraintRegistry = field(default=constraints, repr=False)
    schematics: Dict[str, "Schematic"] = field(default_factory=dict, repr=False)
    primitives: Dict[str, object] = field(
        repr=False,
        default_factory=lambda: {
            "int": int,
            "float": float,
            "complex": complex,
            "decimal": Decimal,
            "number": (Number, Decimal),
            "str": str,
            "bytes": bytes,
            "callable": Callable,
            "mapping": Mapping,
            "sequence": Sequence,
            "list": list,
            "set": set,
            "tuple": tuple,
            "dict": dict,
            "bool": bool,
            "object": object,
            "datetime": datetime,
            "date": date,
            "time": time,
        },
    )

    def primitive(self, name: str, type: Type) -> None:
        self.primitives[name] = type
        self._recompile_schemas()

    def schema(self, value: Union[Dict, Schema, None], name: str = None, strict=None) -> Schema:
        if value is None:
            return None
        if strict is None:
            strict = self.strict
        if isinstance(value, Schema):
            schema = value.copy(env=self, strict=strict, name=name)
        else:
            schema = Schema(value, name=name, env=self, strict=strict)
        key = schema.name or hash(schema)
        self.schemas[key] = schema
        schema = schema.compile()
        return schema

    def get_schema(self, key):
        return self.schemas.get(key, None)

    def get_constraint(self, key):
        return self.constraints.get(native.inflection(key))

    def get_primitive_type(self, name: str) -> Type:
        return self.primitives[name]

    def get_named_schemas(self):
        return {k: v for k, v in self.schemas.items() if isinstance(k, str)}

    ### Internals ###
    def _recompile_schemas(self) -> None:
        for schema in self.schemas.values():
            schema.compile(self)


native = Environment(name="native")
