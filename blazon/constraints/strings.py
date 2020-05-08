import re
from typing import Callable, Set, Any
from numbers import Number
from .base import Constraint, ConstraintFailure, register


### Strings ###
@register(description="must be no longer than {value!r}", require=[str])
def max_length(schema, value):
    def handler(instance, convert=False, partial=False):
        if convert:
            return instance[:value]
        if len(instance) > value:
            raise ConstraintFailure()
        return instance

    return handler


@register(description="must be no shorter than {value!r}", require=[str])
def min_length(schema, value):
    def handler(instance, convert=False, partial=False):
        if len(instance) < value:
            raise ConstraintFailure()
        return instance

    return handler


@register(description="must match the pattern {value!r}", require=[str])
def pattern(schema, value):
    def handler(instance, convert=False, partial=False):
        if re.search(value, instance) is None:
            raise ConstraintFailure()
        return instance

    return handler
