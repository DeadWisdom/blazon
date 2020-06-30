import typing, textwrap
from collections.abc import Mapping, Iterable

### Hash function
def hashish(obj):
    """
    Turns anything into a sort of hash (hash-ish). Sort of, because if an object within it can't be
    hashed, it pretends its id() is the hash. This works for our purposes.
    """
    # First, is it actually hashable? Then good.
    if getattr(obj, "__hash__", None):
        return hash(obj)
    # If it's a mapping, get the hash of it's keys and items
    if isinstance(obj, Mapping):
        hash_keys = hashish(obj.keys())
        hash_values = hashish(obj.values())
        return hash((hash_keys, hash_values))
    # If it's an iterable, hash the tuple of it and it's items
    if isinstance(obj, Iterable):
        return hash(tuple(hashish(x) for x in obj))
    # And here's where we go off the rails and just get the id instead of a good hash.
    # Good enough for gubmint work.
    return id(obj)


### Identity function
def identity(x):
    return x


### Undefined ###
class Undefined:
    def __repr__(self):
        return "<Undefined>"

    def __bool__(self):
        return False


Undefined = Undefined()


### Exceptions ###
class ValidationError(ValueError):
    pass


class SchemaFailure(ValidationError):
    def __init__(
        self,
        schema,
        constraints=None,
        message="could not validate the instance against the schema",
    ):
        self.schema = schema
        self.context = dict(schema.__dict__, schema=schema)
        self.constraints = constraints or {}
        self.message = message
        self.sub_errors = {}

    def __str__(self):
        return self.format()

    def format(self, prefix="  ", depth=0):
        parts = [(prefix * depth) + self.message.format(self.context)]
        for name, error in (self.sub_errors or {}).items():
            parts.append(error.format(prefix, depth + 1))
        return "\n".join(parts)


class ConstraintFailure(ValidationError):
    def __init__(self, message=None, constraint=None, sub_errors=None, path=[], schema=None):
        self.message = message
        self.constraint = constraint
        self.sub_errors = sub_errors
        self.path = path or []
        self.schema = schema

    def __repr__(self):
        return f"{self.__class__.__name__}({self.get_message()})"

    def get_message(self):
        err = self.message or ""
        parts = [err]
        if self.path:
            path = "/".join(self.path)
            parts.insert(0, path)
        if self.schema and self.schema.name:
            parts.insert(0, self.schema.name)
        return " -- ".join(parts)

    def __str__(self):
        parts = [self.get_message()]
        if self.sub_errors:
            if isinstance(self.sub_errors, dict):
                for sub, err in self.sub_errors.items():
                    err = textwrap.indent(str(err), "    ")
                    parts.append(f"  - {sub}:\n{err}")
            else:
                for err in self.sub_errors:
                    # err = textwrap.indent(str(err), "    ")
                    parts.append(f"  - {err}")
        return "\n".join(parts)


class SchemaValidationResult(ValidationError):
    def __init__(self, schema, instance, errors):
        self.schema = schema
        self.instance = instance
        self.errors = errors
        self.success = True
        for constraint, error in errors.items():
            if error is not None:
                self.success = False
                break

    def __bool__(self):
        return self.success

    def items(self):
        return self.errors.items()

    def __iter__(self):
        return iter(self.items())

    def __repr__(self):
        return f"{self.__class__.__name__}(success={self.success})"

    def __str__(self):
        return f"{self.__class__.__name__}:{self.format()}"

    def format(self):
        if self.success:
            return "Schema valid."

        lines = [
            "Could not validate the instance against the schema.",
            "",
            "Instance:",
            f"  {self.instance!r}",
            "" "Errors:",
        ]

        for constraint, err in self:
            lines.append(f"  {err!s}")

        return "\n".join(lines)

    def print_errors(self):
        print(self.format())


class ConstraintKeyError(RuntimeWarning):
    """The constraint was not found in the environment"""


class ConstraintNotApplicable(RuntimeWarning):
    """A constraint was added to a schema but doesn't apply"""


class SchemaCompilationError(RuntimeError):
    """An error durring schema compilation"""
