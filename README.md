# Blazon

Blazon is a library for assuring data structure and format.

It is useful for both processing runtime data like from a web request, and also for type-hinting.
It defines a general schema system that can be translated into multiple other systems, notably
JSON Schema. And includes tools to transform data, and translate schemas between systems.

_Project Status_: This project is currently in a review stage. All comments are welcome, please
leave them as issues on the [github project](https://github.com/DeadWisdom/blazon).

## Data Conversion

Unlike most JSON Schema tools, Blazon's primary goal is to _convert_ the data instead of merely
validating it-- though it can do both. The idea is that usually we don't care whether the data
coming in is correct, we just want it to be correct by the time we use it.

An analogy: I don't care about the shape of the cookie dough as it enters the cutter, I only care
that it comes out as right shape.

A simple example:

```python
import blazon, json

with open("users.json") as o:
  user_data = json.load(o)

user_schema = blazon.json.schema({
  'properties': {
    'name': {'type': 'string'},
    'email': {'type': 'string', 'format': 'email'}
    'age': {'type': 'number', 'minValue': 0, 'default': 42},
  },
  'required': ['name', 'email']
})

users = [user_schema(item) for item in user_data]
```

Now we can be sure that all users have 3 properties:

- name: a string value
- age: a number value that is 0 or higher
- email: a string that is formatted like an email

`blazon.json.schema()` takes any JSON Schema as its argument, and returns a Schema() object, which
is a callable that converts the data.

## Validation

If user_data does not conform, it will raise a ValidationError, which is a subclass of ValueError:

    >>> user_schema(user_data)
    Traceback (most recent call last):
        ...
    ValidationError: name is required

However, since Blazon's general use case is conversion, user_data might not actually conform if it is
reasonably able to be converted to match the schema. This is fits most use-cases, but if you are
trying to specifically validate rather than convert, you can use `validate()`":

TODO: FIX THIS

    >>> user_schema.validate(user_data)
    Traceback (most recent call last):
        ...
    ValidationError: name is required

Either way we ensure that `user_data` matches our schema but the latter will be picky about the
input.

Also you can simply query to see if it validates:

    >>> if user_schema.validate(user_data):
    ...    print("Valid!")
    Valid!

The `Schema.validate()` method actually returns a `SchemaValidationResult` object which will only
evaluate as truthy if validation was successful. It also has information about each field or
constraint that failed.

Note: if your goal is simply JSON validation, and don't need the flexibility or conversion offered
by Blazon, then [fastjsonschema](https://github.com/horejsek/python-fastjsonschema) is around 2-5
times faster.

## Partial Conversion / Validation

We can also do "partial" validation. Often, you want to represent half of an object,
that is an object that doesn't have all of its fields. Whether that's from an update, a PATCH
operation, or because you have a representation that is specifically omitting pieces that
are memory intensive or too much to put on the wire. In most systems you have to represent this with
a separate schema, and that causes all sorts of trouble and is just no fun.

It's real easy, we simply add `partial=True` to our conversion or validation methods, and it simply
doesn't run validation with constraints like 'required'. Using the `user_schema` from above:

    >>> partial_user = user_schema({
      'email': 'person@example.com',
      'age': 24
    }, partial=true)

And so it doesn't raise an error even though "name" is a required field.

Note: this design has a trade off that validated schemas can 'get through' so to speak. So it's good
practice to name partially validated schemas as such, or otherwise track them through.

## Schematics

Schematics are a way of representing schemas as Python classes. They work like dataclasses, but
they also seamlessly interact with an environment like JSON Schema, meaning you can easily represent
their schema. Finally, since they are python types, they are useful for type-hinting via the
`typing` module.

An example:

```python
from blazon import Schematic, field
from shortuuid import uuid

class Character(Schematic):
    name: str
    id : str = field(default_factory=uuid)
    health: int = field(minimum=0, default=100)
    tags: [str]

def damage(char: Character, amount : int):
    char.health -= amount

bob = Character(name="Bob")
damage(bob, 10)
assert bob.health == 90
```

So this Character class now makes enforces specific properties. As might gather, `id` is a string,
with a default value that is a random shortuuid; `name` is a required string, `health` is an integer
that may not go below 0, will default to 100; and `tags` is a list of strings, though it is not
required, since lists default to an empty list as their value.

This Character schematic can then be used normally, and is validated as used:

    >>> char = Character()
    ValidationError: ...

    >>> char = Character(name="Brenda", health=21)
    Character(name="Brenda")

    >>> char.health = -5
    ValidationError: ...

We can easily export it:

    >>> char = Character(name="Tom", id="vytxeTZskVKR7C7WgdSP3d")
    Character(name="Tom")

    >>> char.marshal('json')
    {"name": "Tom", "health": 100, "id": "vytxeTZskVKR7C7WgdSP3d", "tags": []}

    >>> char.marshal('json', partial=True)
    {"name": "Tom", "id": "vytxeTZskVKR7C7WgdSP3d"}

As you can see, we get our data now as a jsonable dictionary. When we marshal it, we get all the
data, but we can also use `partial=True` to get only the fields we set and are not default.

Speaking of partials, we can also create partial schematics:

    >>> char = Character.partial(age=21)
    Character(age=21)

    >>> char.is_partial()
    True

    >>> char.is_valid()
    False

    >>> char.is_valid(partial=True)
    True
    ```

They can also simply use any JSON Schema definition that you give them, for instance one that is
in a yaml file.

```yaml
# Monster.yaml
name: Monster
properties:
  name:
    type: string
  level:
    type: number
    default: 1
```

```python
from blazon import Schematic, json

class Monster(Schematic):
    __schema__ = json.from_file('Monster.yaml')

kate_monster = Monster(name="Kate")
assert kate_monster.level == 1
```

You could likewise use a json file.

Finally, as you can see, you can directly assign the `__schema__` to the Schematic, and we can
interact with it, the same:

    >>> Character.__schema__
    Schema({ "name": "Character", ... })

## Environment

Blazon supports multiple "environments". Each environment can use different constraints, types, and
named schemas. Currently the only two environments out of the box are called `blazon.json`
and `blazon.native` for using expressing JSON Schemas and a similar native python systems,
respectively.

Aspects that are tracked in environments:

- Named schemas: used when a schema is referenced by another
- Inflection: does the system use camel-case, underscores, etc.
- Primitive Types: e.g. int, string, array, object, etc.
- Constraints: The various constraints defined like 'required', 'minValue', 'properties', etc.
- Maps to other environment: To allow marshalling data and translating schemas from one environment
  to the next

The hope is to grow our environments to express many more systems, e.g. Postgres, AWS DynamoDB,
Protocol Buffers, etc. Every schema system that can be distilled similarly as a set of a
constraints should be able to be expressed in Blazon and that's when the fun begins.

If the systems can be expressed generally, we can pass not only data seamlessly between various
systems, but also the schemas themselves. This will let us connect heterogeneous systems simply
by mapping schemas and constraints from one to the next.

## Features Missing

- Schema $ref resolution
- Generating JSON Schemas with $ref and other $special properties
- Type-hint plugins for mypy and others to treat the objects like dataclasses based on the schemas
- Schema translation

... I think that's it.

# Advanced Topics

These advanced topics go into the various actions that are taken on data in Blazon. We try to
codify the language here so that it's consistent.

## Validation

Validation is the process of deciding whether a piece of data fits a schema.

Does the cookie match the cookie cutter?

## Conversion

Conversion is the process of taking data that fits one schema and making it fit another.

Cut the cookie dough out with the cookie cutter.

Often the original schema is undefined, like whatever the client sent you. The new schema is
usually well defined and fits the system.

This can either be lossless or not (lossy), meaning we can lose data as it converts; in other
words we might lose dough when we cut it.

## Marshalling

Marshalling is a act of taking data from one environment to another, e.g. native to json.

Take the cookie and put it through a Play-Doh press.

This is also a conversion (one schema to another), but the schemas are isomorphic but exist
within the context of two separate environments.

## Schema Mapping

Creating mappings between schemas allows us to simply convert data between them. The schemas
can also be in different environments, in which case we are also easily marshalling as well.

Pick a cookie cutter and a Play-Doh cutter and decide they make the same shape.

## Schema Translation

Schema translation is the act of moving a _schema_ from one environment to the other.

Take the cookie cutter, make a corresponding Play-Doh press.

## Constraint Mapping

To do accurate schema translation, we need constraint mapping and type mapping between the
environments. Since a schema can be represented by a set of constraints, mapping constraints
from one environment to another means we can accurately translate schemas. And since the
translated schema is isomorphic, it also means we can marshal data automatically.

Decide that the shape of the cookie cutter can be the same shape in the Play-Doh press.

## Serialization

Serialization is the act of changing the representation of an object into some serial form
usually for transfer over a network or os device.

Look at the cookie, describe it in a text to your friend.

Often serialization is done after transformation, e.g. take a Python object, transform it to
something JSON-like, then serialize it to actual JSON.

Tangent: A _blazon_ in heraldry is a description of a design for a shield, crest, coat of arms, etc.
By having a codified system, which produced texts like [Azure, a bend
or](https://en.wikipedia.org/wiki/Blazon#/media/File:Azure,_a_bend_Or.svg), or [Party per pale
argent and vert, a tree eradicated
counterchanged](https://en.wikipedia.org/wiki/Blazon#/media/File:Wappen_Behnsdorf.png), people could
describe their designs and have them rendered at great distances or by artists that were not
necessarily familiar with them. This was a way of serializing designs.

## Adapters / Coercion

Type coercion is the act of indicating to a compiler or interpreter, that a variable is a
different type than what it is. Really a statically typed language thing.

Let's pretend the cookie is a ninja throwing star.

Making an Adapter is the process of proxying or otherwise wrapping an object to look,
structurally, like another type. This let's us act like it's one type, but really it's still
the other. It's used much more in dynamically typed languages where we can do duck-typing.

Wrap the cookie in tinfoil so we can use it like a throwing star.

For our purposes, if we can create an adapter for a type, we can then apply constraints to it
that were designed for a different type altogether.
