import re
import itertools
import ipaddress
import inflection
import logging
import collections
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping, Sequence, Iterable

from .base import Schema, System, Constraint
from .helpers import ValidationError, Undefined

system = json_schema = System(
    name = "json",
    name_inflection = lambda x: inflection.camelize(x.replace('-', '_'), False),
    primitives={
        'integer': int,
        'number': float,
        'string': str,
        'array': list,
        'object': dict,
        'boolean': bool,
        'null': (lambda x: None)
    })
  

### All Primitives ###
@system.constraint(None)
class Type(Constraint):
    description = "must be of type {value!r}"

    def compile(self, system):
        if isinstance(self.value, str):
            try:
                self._type = self.schema.system.primitives[self.value]
            except KeyError:
                name = system.name or repr(system)
                raise ValueError(f"Unknown primitive type, {name} system has no primitive {self.value!r}")
        else:
            self._type = self.value

    def __call__(self, instance, validate=False, partial=False):
        if hasattr(self.value, '__schema__'):
            self._type = self.value.__schema__

        if isinstance(self._type, Schema):
            if validate:
                return self._type(instance, validate=validate)
            else:
                return self._type(instance)

        elif isinstance(instance, self._type):
            return instance

        if validate:
            self.fail()

        try:
            return self._type(instance)
        except TypeError:
            self.fail()


@system.constraint(None)
class Enum(Constraint):
    description = "must be one of: {value!r}"

    def compile(self, system):
        self._choices = set(self.value)

    def __call__(self, instance, validate=False, partial=False):
        if instance not in self._choices:
            self.fail()
        return instance


@system.constraint(None)
class Const(Constraint):
    description = "must be {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            self.assertEqual(instance, self.value)
        return self.value


### Numbers / Intgers ###
@system.constraint(['number', 'integer'])
class MultipleOf(Constraint):
    description = "must be a multiple of {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        self.assertEqual(instance % self.value, 0)
        return instance


@system.constraint(['number', 'integer'])
class Maximum(Constraint):
    references = ['exclusive_maximum']
    description = "must be no larger than {value!r}"
    description_if_exclusive = "must be larger than {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if self.schema.get_constraint_value('exclusive_maximum', False):
            if instance >= self.value:
                self.fail()
        else:
            if instance > self.value:
                if validate:
                    self.fail()
                return self.value
        return instance

    def describe(self):
        if self.schema.get_constraint_value('exclusive_maximum', False):
            super().describe(self.description_if_exclusive)
        return super().describe()


@system.constraint(['number', 'integer'])
class ExclusiveMaximum(Constraint):
    pass


@system.constraint(['number', 'integer'])
class Minimum(Constraint):
    references = ['exclusive_minimum']
    description = "must be no smaller than {value!r}"
    description_if_exclusive = "must be smaller than {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if self.schema.get_constraint_value('exclusive_minimum', False):
            if instance <= self.value:
                self.fail()
        else:
            if instance < self.value:
                if validate:
                    self.fail()
                return self.value
        return instance

    def describe(self):
        if self.schema.get_constraint_value('exclusive_maximum', False):
            super().describe(self.description_if_exclusive)
        return super().describe()


@system.constraint(['number', 'integer'])
class ExclusiveMinimum(Constraint):
    pass


### Strings ###
@system.constraint(['string'])
class MaxLength(Constraint):
    description = "must be no longer than {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            self.assertTrue(len(instance) <= self.value)
        return instance[:self.value]


@system.constraint(['string'])
class MinLength(Constraint):
    description = "must be longer than {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        self.assertTrue(len(instance) >= self.value)
        return instance


@system.constraint(['string'])
class Pattern(Constraint):
    description = "must match the pattern {value!r}"

    def __call__(self, instance, validate=False, partial=False):
        self.assertNotNone(re.search(self.value, instance))
        return instance


### Array Types ###
@system.constraint(['array'])
class Items(Constraint):
    description = "must match the pattern {value!r}"

    errors = {
        "length": "{instance!r} does not have as many items as {value!r}",
        "each": "{instance!r} does not match the schemas {value!r}",
        "valid": "{instance!r} does not match the schema {value!r}",
        "additional": "{instance!r} has more items than {value!r} and additionalItems is false",
    }

    def compile(self, system):
        self._all_items_must_be = None
        self._items_must_be_in_order = None

        if isinstance(self.value, Sequence):
            self._items_must_be_in_order = [system.schema(v) for v in self.value]
        else:
            self._all_items_must_be = system.schema(self.value)

    def get_max_items_allowed(self):
        if self._all_items_must_be:
            return None
        return len(self._items_must_be_in_order)

    def pairs(self, instance):
        if self._all_items_must_be:
            return itertools.zip_longest(instance, (), fillvalue=self._all_items_must_be)
        return itertools.zip_longest(instance, self._items_must_be_in_order, fillvalue=Undefined)

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            errors = {}
            for index, (item, schema) in enumerate(self.pairs(instance)):
                if schema is Undefined:
                    break
                if item is Undefined:
                    self.fail()
                result = schema.validate(item, partial=partial)
                if not result:
                    errors[f"item {index}"] = result    
            if errors:
                self.fail(errors)
            return instance
        else:
            results = []
            for item, schema in self.pairs(instance):
                if schema is Undefined:
                    break
                if item is Undefined:
                    self.fail()
                results.append( schema(item, partial=partial) )
            return results


@system.constraint(['array'])
class AdditionalItems(Constraint):
    references = ['items']
    description_schema = "all additional items must match the subschema"
    description_true = "may have additional items"
    description_false = "must not have additional items"

    def compile(self, system):
        self._additional_items_allowed = True
        self._additional_items_schema = None

        if isinstance(self.value, dict) or isinstance(self.value, Schema):
            self._additional_items_schema = system.schema(self.value)
        elif self.value is True:
            self._additional_items_allowed = True
        elif self.value is False:
            self._additional_items_allowed = False
        else:
            raise ValueError("Value of constraint must be a dict describing a schema, False, or True.")

    def pairs(self, instance, num_handled):
        if num_handled is None:
            return itertools.zip_longest(instance, (), fillvalue=self._additional_items_schema)
        else:
            return itertools.zip_longest(instance, [None] * num_handled, fillvalue=self._additional_items_schema)

    def __call__(self, instance, validate=False, partial=False):
        items = self.schema.get_constraint_instance('items', None)
        num_handled = items.get_max_items_allowed() if items else 0

        if self._additional_items_allowed is False:
            if len(instance) > num_handled:
                self.fail()
        else:
            if len(instance) <= num_handled:
                return instance

        if validate:
            errors = {}
            for index, (item, schema) in enumerate(self.pairs(instance, num_handled)):
                if schema is None:
                    continue
                result = schema.validate(item, partial=partial)
                if not result:
                    errors[f"item {index}"] = result
            if errors:
                self.fail(errors)
            return instance
        else:
            results = []
            for item, schema in self.pairs(instance, num_handled):
                if schema is None:
                    results.append(item)
                else:
                    results.append(schema(item, partial=partial))
            return results

    def describe(self, msg=None):
        if self._additional_items_schema:
            return super().describe(msg or self.description_schema)
        elif self._additional_items_allowed:
            return super().describe(msg or self.description_true)
        else:
            return super().describe(msg or self.description_false)


@system.constraint(['array'])
class MaxItems(Constraint):
    description = "must have no more than {value!r} items"

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            self.assertTrue(len(instance) <= self.value)
        return instance[:self.value]


@system.constraint(['array'])
class MinItems(Constraint):
    description = "must have at least {value!r} items"

    def __call__(self, instance, validate=False, partial=False):
        self.assertTrue(len(instance) >= self.value)
        return instance


@system.constraint(['array'])
class UniqueItems(Constraint):
    description = "must have have unique items"

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            if len(set(instance)) != len(instance):
                self.fail()
        return list(OrderedDict.fromkeys(instance))


@system.constraint(['array'])
class Contains(Constraint):
    description = "must contain one item that validates against the subschema"

    def compile(self, system):
        self._item_schema = system.schema(self.value)

    def __call__(self, instance, validate=False, partial=False):
        for item in instance:
            if self._item_schema.validate(item):
                return instance
        self.fail()


### Objects ###
@system.constraint(['object'])
class MaxProperties(Constraint):
    description = "must have no more than {value!r} properties"

    def __call__(self, instance, validate=False, partial=False):
        if len(instance.keys()) > self.value:
            self.fail()
        return instance


@system.constraint(['object'])
class MinProperties(Constraint):
    description = "must have no less than {value!r} properties"

    def __call__(self, instance, validate=False, partial=False):
        if len(instance.keys()) < self.value:
            self.fail()
        return instance


@system.constraint(['object'])
class Required(Constraint):
    description = "must have properties with the names: {value!r}"
    
    def compile(self, system):
        if isinstance(self.value, str) or not isinstance(self.value, Iterable):
            raise TypeError(f"'{self.__class__.__name__.lower()}' constraint value must be an iterable other than a string.")
        super().compile(system)
    
    def __call__(self, instance, validate=False, partial=False):
        if partial:
            return instance
        
        for key in self.value:
            if instance.get(key, Undefined) is Undefined:
                self.fail()

        return instance


@system.constraint(['object'])
class Properties(Constraint):
    description = "must have matching properties"

    def compile(self, system):
        result = {}
        for key, subval in self.value.items():
            result[key] = system.schema(subval)
        self._property_schemas = result

    def get_pairs(self, instance):
        """
        Returns pairs of (attribute-key, schema)
        """
        return self._property_schemas.items()

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            errors = {}
            for name, schema in self.get_pairs(instance):
                value = instance.get(name, Undefined)
                if value is Undefined:
                    continue
                result = schema.validate(value)
                if not result:
                    errors[name] = result
            if errors:
                self.fail(errors)
            return instance
        else:
            results = {}
            for name, schema in self.get_pairs(instance):
                value = instance.get(name, Undefined)
                if value is Undefined:
                    continue
                try:
                    results[name] = schema(value)
                except ValidationError as e:
                    e.path.insert(0, '{' + name + '}')
                    raise
            return results


@system.constraint(['object'])
class PatternProperties(Properties):
    description = "properties with names that match the given pattern must match the subschemas"

    def get_pairs(self, instance):
        for key in instance.keys():
            for regex, schema in self._property_schemas.items():
                if re.search(regex, key):
                    yield (key, schema)


@system.constraint(['object'])
class AdditionalProperties(Properties):
    references = ["properties", "patternProperties"]
    description = "additional properties must match the subschema"

    def compile(self, system):
        self._property_schema = system.schema(self.value)

    def get_pairs(self, instance):
        sources = [
            self.schema.get_constraint_instance('properties', None),
            self.schema.get_constraint_instance('patternProperties', None)
        ]
        seen = set()
        for source in sources:
            if source:
                seen.update(key for key, schema in source.get_pairs(instance))
        return ((key, self._property_schema) for key in instance.keys() if key not in seen)
    

@system.constraint(['object'])
class Dependencies(Constraint):
    description = "dependant schemas must validate"

    def compile(self, system):
        self._dependant_requirements = {}
        self._dependant_schemas = {}
        for key, value in self.value.items():
            if isinstance(value, dict) or isinstance(value, Schema):
                self._dependant_schemas[key] = system.schema(value)
            elif isinstance(value, Sequence):
                self._dependant_requirements[key] = [str(x) for x in value]
            else:
                raise ValueError("dependencies constraint requires a mapping of properties to either"
                                " schema or list of required properties, but got this: %r" % value)

    def __call__(self, instance, validate=False, partial=False):
        for key, requirements in self._dependant_requirements.items():
            if key in instance:
                for other_key in requirements:
                    if other_key not in instance:
                        self.fail(message="since {other_key!r} appears, {key!r} must also appear")

        for key, schema in self._dependant_schemas.items():
            if key in instance:
                if validate:
                    if not schema.validate(instance):
                        self.fail(message="dependant validation failed since {key!r} appears")
                else:
                    try:
                        instance = schema(instance)
                    except ValidationError as e:
                        e.path = [f'dependency({key})', name] + e.path
                        raise
        return instance


@system.constraint(['object'])
class PropertyNames(Constraint):
    description = "property names must match the given schema"

    def compile(self, system):
        self._key_schema = system.schema(self.value)

    def __call__(self, instance, validate=False, partial=False):
        for key in instance.keys():
            if not self._key_schema.validate(key):
                self.fail()
        return instance


### Conditional ###
@system.constraint(None)
class If(Constraint):
    references = ["then", "else"]
    description = "if the 'if' schema validates then the 'then' schema must, otherwise the 'else' schema must"
    
    def compile(self, system):
        self._condition = system.schema(self.value)

    def __call__(self, instance, validate=False, partial=False):
        _then = self.schema.get_constraint_instance('then', None)
        _else = self.schema.get_constraint_instance('else', None)

        if self._condition.validate(instance):
            if _then is None:
                return instance
            if validate:
                result = _then._schema_value.validate(instance)
                if not result:
                    self.fail({'then': result}, message="'then' subschema does not validate and must")
            else:
                try:
                    instance = schema(instance)
                except ValidationError as e:
                    e.path = [f'then'] + e.path
                    raise
        else:
            if _else is None:
                return instance
            if validate:
                result = _then._schema_value.validate(instance)
                if not result:
                    self.fail({'else': result}, message="'else' subschema does not validate and must")
            else:
                try:
                    instance = schema(instance)
                except ValidationError as e:
                    e.path = [f'else'] + e.path
                    raise 
        return instance


@system.constraint(None)
class Then(Constraint):
    def compile(self, system):
        self._schema_value = system.schema(self.value)


@system.constraint(None)
class Else(Constraint):
    def compile(self, system):
        self._schema_value = system.schema(self.value)


@system.constraint(None)
class AllOf(Constraint):
    description = "must validate against every subschema"

    def compile(self, system):
        assert self.value, "value must be a list of schemas"
        self._subschemas = [system.schema(item) for item in self.value]

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            errors = {}
            for index, sub in enumerate(self._subschemas):
                result = sub.validate(instance, partial=partial)
                if not result:
                    errors[f"allof({index})"] = result
            if errors:
                self.fail(errors)
        else:
            for sub in self._subschemas:
                instance = sub(instance)
        return instance


@system.constraint(None)
class AnyOf(Constraint):
    description = "must validate with least one subschema"

    def compile(self, system):
        assert self.value, "value must be a list of schemas"
        self._subschemas = [system.schema(item) for item in self.value]

    def __call__(self, instance, validate=False, partial=False):
        if validate:
            success = False
            errors = {}
            for index, sub in enumerate(self._subschemas):
                result = sub.validate(instance, partial=partial)
                if not result:
                    errors[f"anyof({index})"] = result
                else:
                    success = True
            if not success:
                self.fail(errors)
        else:
            for index, sub in enumerate(self._subschemas):
                try:
                    return sub(instance, partial=partial)
                except (TypeError, ValueError):
                    continue
            self.fail()
        return instance


@system.constraint(None)
class OneOf(Constraint):
    description = "must validate with exactly one subschema"

    def compile(self, system):
        assert self.value, "value must be a list of schemas"
        self._subschemas = [system.schema(item) for item in self.value]

    def __call__(self, instance, validate=False, partial=False):
        success = set()
        errors = {}
        for index, sub in enumerate(self._subschemas):
            result = sub.validate(instance, partial=partial)
            if not result:
                errors[f"anyof({index})"] = result
            else:
                success.add(sub)
        if len(success) != 1:
            self.fail(errors)
        if not validate:
            return success.pop()(instance, partial=partial)
        return instance


@system.constraint(None)
class Not(Constraint):
    description = "must *not* validate against the subschema"

    def compile(self, system):
        self._condition = system.schema(self.value)

    def __call__(self, instance, validate=False, partial=False):
        if self._condition.validate(instance):
            self.fail()
        return instance


### Format ###
date_re = re.compile(r'^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$')
time_re = re.compile(r'^\s*(\d\d):(\d\d):(\d\d)(\.(\d+))?([zZ]|(([-+])(\d\d):?(\d\d)))\s*$')
date_time_re = re.compile(r'^\s*(\d\d\d\d)-(\d\d)-(\d\d)[ tT](\d\d):(\d\d):(\d\d)(\.(\d+))?([zZ]|(([-+])(\d\d):?(\d\d)))\s*$')
email_re = re.compile(r'(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])')
hostname_re = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)


@system.constraint(['string'])
class Format(Constraint):
    formats = {}

    def compile(self, system):
        if (self.value == 'datetime'):
            self.value = 'date_time'
        self.value = system.name_inflection(self.value)

    def __call__(self, instance, validate=False, partial=False):
        if self.schema.system.ignore_all_formats:
            return instance
        if self.value in self.schema.system.ignore_these_formats:
            return instance
        fn_name = f'validate_{self.value}'
        fn = getattr(self, fn_name, None)
        if fn is None:
            if fn_name == 'datetime':
                logging.warning(f"unknown format: {self.value} - so it passes - try 'date-time', not 'datetime'.")
            else:    
                logging.warning(f"unknown format: {self.value} - so it passes")
            return
        if not fn(instance):
            self.fail("{instance!r} does not match the format {value!r}")
        return instance

    def validate_dateTime(self, instance):
        return date_time_re.match(instance) is not None

    def validate_date(self, instance):
        return date_re.match(instance) is not None

    def validate_time(self, instance):
        return time_re.match(instance) is not None

    def validate_email(self, instance):
        return email_re.match(instance) is not None

    def validate_hostname(self, instance):
        if len(instance) > 255:
            return False
        if instance[-1] == ".":
            instance = instance[:-1]
        return all(hostname_re.match(x) for x in instance.split("."))

    def validate_ipv4(self, instance):
        try:
            ipaddress.IPv4Address(instance)
            return True
        except ValueError:
            return False

    def validate_ipv6(self, instance):
        try:
            ipaddress.IPv6Address(instance)
            return True
        except ValueError:
            return False

    def validate_uri(self, instance):
        try:
            import rfc3987
        except ImportError:
            logging.warning("package rfc3987 missing - cannot validate uri - so it passes")
            return True
        return rfc3987.match(instance, rule='URI')

    def validate_uri_reference(self, instance):
        try:
            import rfc3987
        except ImportError:
            logging.warning("package rfc3987 missing - cannot validate uri-reference - so it passes")
            return True
        return rfc3987.match(instance, rule='URI_reference')

    def validate_iri(self, instance):
        try:
            import rfc3987
        except ImportError:
            logging.warning("package rfc3987 missing - cannot validate iri - so it passes")
            return True
        return rfc3987.match(instance, rule='IRI')

    def validate_iri_reference(self, instance):
        try:
            import rfc3987
        except ImportError:
            logging.warning("package rfc3987 missing - cannot validate iri-reference - so it passes")
            return True
        return rfc3987.match(instance, rule='IRI_reference')

### Quick Schemas ###
system.Object = system.schema({'type': 'object'})