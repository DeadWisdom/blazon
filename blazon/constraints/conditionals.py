import blazon, re
from collections.abc import Mapping, Iterable
from .base import register, ConstraintFailure, Undefined, ValidationError
from .containers import min_items, max_items


@register(
    name="if",
    description="If the 'if' schema validates then the 'then' schema must also, otherwise the 'else' schema must",
)
def if_condition(schema, value):
    _if = schema.env.schema(value)
    subschema = {
        "then": schema.env.schema(schema.get("then", None)),
        "else": schema.env.schema(schema.get("else", None)),
    }

    def handler(instance, convert=False, partial=False):
        if _if.validate(instance):
            branch = "then"
        else:
            branch = "else"

        if subschema[branch] is None:
            return instance

        try:
            if convert:
                return subschema[branch](instance, partial=partial)
            result = subschema[branch].validate(instance, partial=partial)
            if result:
                return instance
            raise ConstraintFailure(message=f"'{branch}' subschema does not validate and must")
        except ValidationError as e:
            e.path = [branch] + e.path
            raise

    return handler


@register(name="then", description="This schema is applied if the 'if' constraint matches")
def then_conditional(schema, value):
    return None


@register(name="else", description="This schema is applied if the 'if' constraint does not match")
def else_conditional(schema, value):
    return None


@register(description="All of the given schemas need to validate", require=[Iterable])
def all_of(schema, value):
    subschemas = tuple(schema.env.schema(v) for v in value)

    def handler(instance, convert=False, partial=False):
        if convert:
            for sub in subschemas:
                instance = sub(instance, partial=partial)
        else:
            errors = {}
            for index, sub in enumerate(subschemas):
                result = sub.validate(instance, partial=partial)
                if not result:
                    errors[f"allof({index})"] = result
            if errors:
                raise ConstraintFailure(sub_errors=errors)

        return instance

    return handler


@register(description="Any of the given schemas need to validate")
def any_of(schema, value):
    subschemas = tuple(schema.env.schema(v) for v in value)

    def handler(instance, convert=False, partial=False):
        if convert:
            for index, sub in enumerate(subschemas):
                try:
                    return sub(instance, partial=partial)
                except (TypeError, ValueError):
                    continue
                raise ConstraintFailure()
        else:
            success = False
            errors = {}
            for index, sub in enumerate(subschemas):
                result = sub.validate(instance, partial=partial)
                if not result:
                    errors[f"allof({index})"] = result
                else:
                    success = True
            if not success:
                raise ConstraintFailure(sub_errors=errors)

        return instance

    return handler


@register(description="Any of the given schemas need to validate")
def any_of(schema, value):
    subschemas = tuple(schema.env.schema(v) for v in value)

    def handler(instance, convert=False, partial=False):
        if convert:
            for index, sub in enumerate(subschemas):
                try:
                    return sub(instance, partial=partial)
                except (TypeError, ValueError):
                    continue
                raise ConstraintFailure()
        else:
            success = False
            errors = {}
            for index, sub in enumerate(subschemas):
                result = sub.validate(instance, partial=partial)
                if not result:
                    errors[f"allof({index})"] = result
                else:
                    success = True
            if not success:
                raise ConstraintFailure(sub_errors=errors)

        return instance

    return handler


@register(description="Exactly one of the given schemas needs to validate, no more, no less")
def one_of(schema, value):
    subschemas = tuple(schema.env.schema(v) for v in value)

    def handler(instance, convert=False, partial=False):
        success = set()
        errors = {}
        for index, sub in enumerate(subschemas):
            result = sub.validate(instance, partial=partial)
            if not result:
                errors[f"oneof({index})"] = result
            else:
                success.add(sub)
        if len(success) != 1:
            raise ConstraintFailure(sub_errors=errors)
        if convert:
            return success.pop()(instance, partial=partial)
        return instance

    return handler


@register(name="not", description="Must *not* validate against the subschema")
def not_(schema, value):
    condition = schema.env.schema(value)

    def handler(instance, convert=False, partial=False):
        if condition.validate(instance, partial=partial):
            raise ConstraintFailure()
        return instance

    return handler
