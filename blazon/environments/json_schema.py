from inflection import camelize
from ..constraints import constraints
from ..environment import Environment

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
    def from_file(self, file, type=None):
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
                with open(file, 'r') as file:
                    value = yaml.safe_load(file)
        print(self.constraints)
        return self.schema(value)


env = JSONEnvironment(
    name="jsonSchema",
    inflection = json_inflection,
    strict = False,
    constraints = json_constraints,
    primitives = {
        "number": float,
        "integer": int,
        "string": str,
        "object": dict,
        "array": list,
        "boolean": bool,
        "null": None,
    })

schema = env.schema