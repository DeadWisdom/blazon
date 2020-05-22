import itertools
from typing import Callable, Set, Any
from numbers import Number
from collections.abc import Iterable, Mapping, Sized, Sequence
from .base import Constraint, ConstraintFailure, register, Undefined


def matches(left, right, fill=Undefined):
    return


def schema_matches(instance, schemas, fill=Undefined, convert=False):
    results = []
    for v, s in itertools.zip_longest(instance, schemas, fillvalue=fill):
        if s is False:
            raise ConstraintFailure("Instance does not have enough items to match")
        if v is Undefined:
            raise ConstraintFailure("Instance has more items than ")
        if convert:
            if s:
                results.append(s(v))
            else:
                results.append(v)
        else:
            if s:
                results.append(s.validate(v))
            else:
                break
    return results


### Strings ###
@register(
    description="items much match the given schema: {value!r}", require=[Iterable], exclude=[str]
)
def items(schema, value):
    if isinstance(value, Mapping):
        schemas_to_match = []
        additional_items = schema.env.schema(value)
    else:
        schemas_to_match = [schema.env.schema(v) for v in value]
        additional_items = schema.get("additional_items", Undefined)
        if additional_items is not Undefined and additional_items is not False:
            additional_items = schema.env.schema(additional_items)

    def handler(instance, convert=False, partial=False):
        results = schema_matches(instance, schemas_to_match, fill=additional_items, convert=convert)

        if convert:
            return results

        if not all(results):
            raise ConstraintFailure("a sub-schema does not match", sub_errors=results)

    return handler


@register(description=None)
def additional_items(schema, value):
    return None


@register(
    description="sequence must not have more than {value} items", require=[Sized], exclude=[str]
)
def max_items(schema, value):
    def handler(instance, convert=False, partial=False):
        if convert and isinstance(instance, Sequence):
            return instance[:value]
        if len(instance) > value:
            raise ConstraintFailure()
        return instance

    return handler


@register(
    description="sequence must not have less than {value} items", require=[Sized], exclude=[str]
)
def min_items(schema, value):
    def handler(instance, convert=False, partial=False):
        if len(instance) < value:
            raise ConstraintFailure()
        return instance

    return handler


def unique_set(items):
    try:
        return set(items)
    except TypeError:
        return list({repr(i): i for i in items}.values())


@register(description="sequence must not have all unique items", require=[Sized], exclude=[str])
def unique_items(schema, value):
    if "set" in schema.env.primitives:
        return_type = set
    else:
        return_type = list

    def handler(instance, convert=False, partial=False):
        if convert:
            return return_type(unique_set(instance))
        if len(unique_set(instance)) != len(instance):
            raise ConstraintFailure()

    return handler


@register(
    description="sequence must contain an item that matches the schema: {value!r}",
    require=[Sized],
    exclude=[str],
)
def contains(schema, value):
    sub_schema = schema.env.schema(value)

    def handler(instance, convert=False, partial=False):
        for item in instance:
            if sub_schema.validate(item):
                return instance

        raise ConstraintFailure()

    return handler
