import typing


### Hash function
def build_hash(obj, hsh):
    if hasattr(obj, 'get_hash'):
        hsh.update( obj.get_hash().encode() )
    elif isinstance(obj, str):
        hsh.update( obj.encode() )
    elif isinstance(obj, bytes):
        hsh.update( obj )
    elif isinstance(obj, typing.Mapping):
        for k, item in obj.items():
            build_hash(k, hsh)
            build_hash(item, hsh)
    elif isinstance(obj, typing.Iterable):
        for item in obj:
            build_hash(item, hsh)  
    elif hasattr(obj, '__schema__'):
        hsh.update( obj.__schema__.get_hash().encode() )
    else:
        hsh.update(str(hash(obj)).encode())


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
    def __init__(self, schema, constraints=None, message="could not validate the instance against the schema"):
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
            parts.append(error.format(prefix, depth+1))
        return "\n".join(parts)


class ConstraintFailure(ValidationError):
    def __init__(self, constraint, sub_errors=None, path=[], message=None, schema=None):
        self.constraint = constraint
        self.sub_errors = sub_errors
        self.message = message
        self.path = path or []
        self.schema = schema

    def __str__(self):
        err = self.constraint.describe(self.message)
        parts = [err]
        if self.path:
            path = "/".join(self.path)
            parts.insert(0, path)
        if self.schema and self.schema._name:
            parts.insert(0, self.schema._name)
        return " -- ".join(parts)


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
        return f'{self.__class__.__name__}:{self.format()}'

    def format(self):
        if self.success:
            return "Schema valid."

        lines = ["Could not validate the instance against the schema.", 
                  "", 
                  "Instance:", 
                  f"  {self.instance!r}",
                  ""
                  "Errors:"]

        for constraint, err in self:
            lines.append(f"  {err!r}")

        return "\n".join(lines)

    def print_errors(self):
        print(self.format())

