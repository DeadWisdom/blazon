import inflection
from datetime import date, datetime, time
from collections.abc import Mapping, MutableMapping, Sequence, Callable
from numbers import Number
from decimal import Decimal

AnyNumber = (Number, Decimal)

from .base import Schema, System, Constraint
from .helpers import ValidationError, Undefined

system = native = System(
    name="native",
    name_inflection = inflection.underscore,
    primitives={
        'int': int,
        'float': float,
        'complex': complex,
        'decimal': Decimal,
        'number': AnyNumber,
        'str': str,
        'bytes': bytes,
        'callable': Callable,
        'mapping': Mapping,
        'sequence': Sequence,
        'list': list,
        'set': set,
        'tuple': tuple,
        'dict': dict,
        'bool': bool,
        'object': object,
        'datetime': datetime,
        'date': date,
        'time': time
    })


from .json_schema import system as json


#system.map_transformations({
#    'json.integer': {'int': int, 'decimal': Decimal, 'number': int},
#    'int': {'json.integer': int, 'json.string': str},
#    'decimal': {'json.integer': int, 'json.string': str},
#    'number': {'json.integer': float, 'json.string': str}
#
#    'json.string': {'str': str, 'bytes': lambda x: x.encode()},
#    'bytes': {'json.string': {lambda x: x.decode()},
#    'str': {'json.string': str, 'json.int': int},
#
#    'json.object': {'dict': dict, 'sequence': },
#
#    'json.array': {''
#})


system.borrow_constraint(json, 'type', primitives=None)
system.borrow_constraint(json, 'enum', primitives=None)
system.borrow_constraint(json, 'const', primitives=None)

system.borrow_constraint(json, 'multiple_of', primitives=['int', 'float', 'number'])
system.borrow_constraint(json, 'maximum', primitives=['int', 'float', 'number'])
system.borrow_constraint(json, 'exclusive_maximum', primitives=['int', 'float', 'number'])
system.borrow_constraint(json, 'minimum', primitives=['int', 'float', 'number'])
system.borrow_constraint(json, 'exclusive_minimum', primitives=['int', 'float', 'number'])

system.borrow_constraint(json, 'max_length', primitives=['str'])
system.borrow_constraint(json, 'min_length', primitives=['str'])
system.borrow_constraint(json, 'pattern', primitives=['str'])

system.borrow_constraint(json, 'items', primitives=['sequence', 'list', 'tuple'])
system.borrow_constraint(json, 'additional_items', primitives=['sequence', 'list', 'tuple'])
system.borrow_constraint(json, 'max_items', primitives=['list', 'tuple'])
system.borrow_constraint(json, 'min_items', primitives=['list', 'tuple'])
system.borrow_constraint(json, 'unique_items', primitives=['sequence', 'list', 'tuple'])
system.borrow_constraint(json, 'contains', primitives=['sequence', 'list', 'tuple'])

system.borrow_constraint(json, 'max_properties', primitives=['dict'])
system.borrow_constraint(json, 'min_properties', primitives=['dict'])
system.borrow_constraint(json, 'required', primitives=['dict'])
system.borrow_constraint(json, 'properties', primitives=['dict'])
system.borrow_constraint(json, 'pattern_properties', primitives=['dict'])
system.borrow_constraint(json, 'additional_properties', primitives=['dict'])
system.borrow_constraint(json, 'dependencies', primitives=['dict'])
system.borrow_constraint(json, 'property_names', primitives=['dict'])

system.borrow_constraint(json, 'if', primitives=None)
system.borrow_constraint(json, 'then', primitives=None)
system.borrow_constraint(json, 'else', primitives=None)

system.borrow_constraint(json, 'all_of', primitives=None)
system.borrow_constraint(json, 'any_of', primitives=None)
system.borrow_constraint(json, 'one_of', primitives=None)
system.borrow_constraint(json, 'not', primitives=None)

system.borrow_constraint(json, 'format', primitives=['str'])


@system.constraint(['object'])
class HasAttrs(Constraint):
    description = "must have the following attrs: {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        for attr in self.value:
            if not hasattr(instance, attr):
                self.fail()
        return instance


@system.constraint(['object', 'dict'])
class InstanceOf(Constraint):
    description = "must be an instance of: {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if isinstance(instance, self.value):
            return instance
        elif isinstance(instance, dict):
            return self.value(**instance)
        elif not validate:
            try:
                return self.value(instance)
            except:
                raise
        self.fail()


@system.constraint(['callable'])
class SubclassOf(Constraint):
    description = "must be a subclass of: {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if isinstance(instance, type) and issubclass(instance, self.value):
            return instance
        self.fail()


@system.constraint(['object', 'dict'])
class SchemaValue(Constraint):
    description = "must be a schema or describe a schema"

    def __call__(self, instance, validate=False, partial=False):
        if isinstance(instance, Schema):
            return instance
        elif hasattr(instance, '__schema__'):
            return instance.__schema__
        elif isinstance(instance, dict):
            return Schema(instance, system=self.schema.system)
        else:
            self.fail()
