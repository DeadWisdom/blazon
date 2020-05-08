from typing import Callable, Set, Any
from numbers import Number
from .base import Constraint, ConstraintFailure, register


@register(description="must be a multiple of {value!r}", require=[Number])
def multiple_of(schema, value):
    def handler(instance, convert=False, partial=False):
        if instance % value != 0:
            raise ConstraintFailure()
        return instance

    return handler


@register(description=None, require=[Number])
def maximum(schema, value):

    if schema.get("exclusive_maximum", False):

        def handler(instance, convert=False, partial=False):
            if instance < value:
                return instance
            raise ConstraintFailure(f"must be smaller than {value!r}")

    else:

        def handler(instance, convert=False, partial=False):
            if instance <= value:
                return instance

            if convert:
                return value

            raise ConstraintFailure(f"must be no larger than {value!r}")

    return handler


@register(description=None)
def exclusive_maximum(schema, value):
    return None


@register(description=None, require=[Number])
def minimum(schema, value):

    if schema.get("exclusive_minimum", False):

        def handler(instance, convert=False, partial=False):
            if instance > value:
                return instance
            raise ConstraintFailure(f"must be larger than {value!r}")

    else:

        def handler(instance, convert=False, partial=False):
            if instance >= value:
                return instance

            if convert:
                return value

            raise ConstraintFailure(f"must be no smaller than {value!r}")

    return handler


@register(description=None)
def exclusive_minimum(schema, value):
    return None
