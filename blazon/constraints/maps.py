import blazon, re
from collections.abc import Mapping, Iterable
from .base import register, constraints, ConstraintFailure, Undefined, ValidationError
from .containers import min_items, max_items

### Need the type of the regex.  In 3.7 we have re.Pattern, but in 3.6 we have to get it weird.
try:
    RegEx = re.Pattern
except NameError:
    RegEx = type(re.compile("-"))


### Helpers ###
def regex(source):
    """Return a regex for the source, if the source is a regex then just return it."""
    if isinstance(source, RegEx):
        return source
    return re.compile(source)


def any_matches(name, patterns):
    for r in patterns:
        if r.search(name):
            return True
    return False


### Constraints ###
constraints.add(
    min_items,
    name="min-entries",
    description="must have at least {value} entries",
    require=[Mapping],
)

constraints.add(
    max_items,
    name="max-entries",
    description="must have no more than {value} entries",
    require=[Mapping],
)


@register(description="must have the required keys: {value!r}", require=[Mapping])
def required(schema, value):
    def handler(instance, convert=False, partial=False):
        if partial:
            return instance

        value.sort()

        for key in value:
            if key not in instance:
                raise ConstraintFailure(f"must have the required entry: {key}")

        return instance

    return handler


### Entries/JSON Schema: Properties ###
def entry_handler(generator):
    def handler(instance, convert=False, partial=False):
        instance_keys = set(instance.keys())
        if convert:
            for name, sub_schema, value in generator(instance):
                if sub_schema is False:
                    raise ConstraintFailure("additional properties not allowed: %r" % name)
                if sub_schema is True:
                    instance[name] = value
                if hasattr(value, "__schema__"):
                    value = value.__dict__
                try:
                    instance[name] = sub_schema(value)
                except ValidationError as e:
                    e.path.insert(0, "{" + name + "}")
                    raise
            return instance

        errors = {}
        for name, sub_schema, value in generator(instance):
            if sub_schema is False:
                raise ConstraintFailure("additional properties not allowed")
            if sub_schema is True:
                continue
            result = sub_schema.validate(value)
            if not result:
                errors[name] = result
        if errors:
            raise ConstraintFailure("not all entries match", sub_errors=errors)
        return instance

    return handler


@register(description="must have the matching items", require=[Mapping])
def entries(schema, value):
    schema_map = dict((k, schema.env.schema(v)) for k, v in value.items())

    for name, schema in schema_map.items():
        if schema is None:
            raise RuntimeError("Schema value is None")

    def generator(instance):
        for name, schema in schema_map.items():
            if name in instance:
                yield name, schema, instance[name]

    return entry_handler(generator)


@register(
    description="entries with names that match the given pattern must match the sub-schemas: {value!r}",
    require=[Mapping],
)
def pattern_entries(schema, value):
    regex_schema_map = dict((regex(src), schema.env.schema(v)) for src, v in value.items())

    def generator(instance):
        for name, value in instance.items():
            for regex, schema in regex_schema_map.items():
                if regex.search(name):
                    yield name, schema, value

    return entry_handler(generator)


@register(
    description="additional properties must match the sub-schema: {value!r}", require=[Mapping],
)
def additional_entries(schema, value):
    patterns = [regex(k) for k in schema.get("pattern_entries", {}).keys()]
    names = set(k for k in schema.get("entries", {}).keys())
    if value is False or value is True:
        match_schema = value
    else:
        match_schema = schema.env.schema(value)

    def generator(instance):
        for name, value in instance.items():
            if name in names or any_matches(name, patterns):
                continue
            yield name, match_schema, value

    return entry_handler(generator)


@register(
    description="dependant schemas must validate", require=[Mapping],
)
def dependencies(schema, value):
    dependant_schemas = {}
    dependant_requirements = {}

    for key, value in value.items():
        if isinstance(value, Mapping):
            dependant_schemas[key] = schema.env.schema(value)
        elif isinstance(value, Iterable):
            dependant_requirements[key] = [str(x) for x in value]
        else:
            raise ValueError(
                "dependencies constraint requires a mapping of properties to either"
                " schema or list of required properties, but got this: %r" % value
            )

    def handler(instance, convert=False, partial=False):
        for key, requirements in dependant_requirements.items():
            if key in instance:
                for other_key in requirements:
                    if other_key not in instance:
                        raise ConstraintFailure(
                            message="since {other_key!r} appears, {key!r} must also appear"
                        )

        for key, schema in dependant_schemas.items():
            if key in instance:
                if not convert:
                    if not schema.validate(instance):
                        raise ConstraintFailure(
                            message="dependant validation failed since {key!r} appears"
                        )
                else:
                    try:
                        instance = schema(instance)
                    except ValidationError as e:
                        e.path = [f"dependency({key})", name] + e.path
                        raise
        return instance

    return handler


@register(
    description="entry names must match the given schema", require=[Mapping],
)
def entry_names(schema, value):
    name_schema = schema.env.schema(value)

    def handler(instance, convert=False, partial=False):
        for key in instance.keys():
            if not name_schema.validate(key):
                raise ConstraintFailure()

    return handler
