import os
from abc import ABC
from inflection import camelize
from ..constraints import constraints
from ..environment import Environment
from dataclasses import MISSING


### Resolver ###
class Resolver(ABC):
    def load_file(self, env, filename, name=None):
        pass


class FileResolver:
    def __init__(self, root=".", allow_backwards=False):
        self.root = os.path.abspath(root)
        self.allow_backwards = False

    def read(self):
        with open(self.path) as file:
            this

    # def load_json(self, obj):

    # def load_yaml(self, obj):

    # def


class ObjectResolver:
    def __init__(self, file):
        self.file = file


json_inflection = lambda x: camelize(x.replace("-", "_"), False)

json_constraints = constraints.clone(
    inflection=json_inflection,
    include=[
        "additionalItems",
        "allOf",
        "anyOf",
        "const",
        "contains",
        "dependencies",
        "else",
        "enum",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "format",
        "if",
        "items",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "multipleOf",
        "not",
        "oneOf",
        "pattern",
        "required",
        "then",
        "type",
        "uniqueItems",
    ],
    map={
        "additionalProperties": "additional_entries",
        "maxProperties": "max_entries",
        "patternProperties": "pattern_entries",
        "minProperties": "min_entries",
        "properties": "entries",
        "propertyNames": "entryNames",
    },
)


class JSONEnvironment(Environment):
    resolver: Resolver = FileResolver()

    def resolve_schema(self, path):
        name = path.rsplit("/", 1)[-1]
        if name in self.schemas:
            return self.schemas[name]
        ref_schema = find_reference(self._file, path)
        return self.schema(ref_schema, name=name)

    def from_file(self, file, type=None, name=MISSING, load_references=True, resolver=None):
        if type is None:
            if isinstance(file, str) and (file.endswith(".yaml") or file.endswith(".yml")):
                type = "yaml"
            else:
                type = "json"

        if type not in ("yaml", "json"):
            raise TypeError("Supported types: 'yaml' or 'json'")

        if type == "json":
            import json

            if hasattr(file, "read"):
                value = json.load(file)
            else:
                with open(file, "r") as file:
                    value = json.load(file)
        else:
            import yaml

            if hasattr(file, "read"):
                value = yaml.safe_load(file)
            else:
                with open(file, "r") as file:
                    value = yaml.safe_load(file)

        self._file = value

        return self.schema(value, name=name)  # , resolver=file_resolver(value, filename=file)


env = JSONEnvironment(
    name="jsonSchema",
    inflection=json_inflection,
    strict=False,
    constraints=json_constraints,
    primitives={
        "number": float,
        "integer": int,
        "string": str,
        "object": dict,
        "array": list,
        "boolean": bool,
        "null": None,
    },
)

schema = env.schema


def find_reference(root, path):
    if not path:
        return root
    if isinstance(path, str):
        path = path.split("/")
    head = path[0]
    if head == "#":
        return find_reference(root, path[1:])
    return find_reference(root[head], path[1:])


def reference(schema, value):
    return schema.env.resolve_schema(value)


json_constraints.add(reference, name="$ref", description="special constraint to load references")
