import os, pytest
import blazon

from blazon import Schematic, field, json


def test_schema():
    class Person(Schematic):
        name: str
        age: int = 42

    assert Person.__schema__.value == {
        "entries": {"name": {"type": str}, "age": {"type": int, "default": 42},},
        "required": ["name"],
    }

    p = Person(name="Bob")

    assert p.name == "Bob"
    assert p.age == 42


def test_extra_fields():
    class Person(Schematic):
        name: str
        age: int = 42

    with pytest.raises(AttributeError):
        # Extra is not defined
        Person(extra=None)

    p = Person()
    p.extra = 2  # You can assign it though


def test_setters():
    class Person(Schematic):
        name: str
        age: int = 42

    p = Person()
    p.name = 2
    assert p.name == "2"

    p.age = "2"
    assert p.age == 2

    with pytest.raises(ValueError):
        p.age = "asdf"


def test_set_value():
    class Person(Schematic):
        name: str
        age: int = 42

    p = Person()
    p.set_value({"name": 2})
    assert p.name == "2"

    p.set_value({"age": "2"})
    assert p.age == 2

    p.set_value({"name": 3, "age": "4"})
    assert p.name == "3"
    assert p.age == 4

    with pytest.raises(ValueError):
        p.set_value({"age": "asdf"})


def test_validate():
    class Person(Schematic):
        name: str
        age: int = 42

    p = Person(name="Bob")
    assert p.validate()

    # Name is required
    p = Person()
    assert not p.validate()


def test_custom_schema():
    class Person(Schematic):
        __schema__ = blazon.schema(
            {
                "entries": {
                    "name": {"type": str},
                    "age": {"type": int, "minimum": 0, "default": 42},
                },
                "required": ["name"],
            }
        )

    p = Person(name=2)
    assert p.name == "2"
    assert p.age == 42

    p.age = -1
    assert p.age == 0


def test_fields():
    class Person(Schematic):
        name: str
        age: int = field(default=42, minimum=0)

    p = Person()
    p.age = -1
    assert p.age == 0


def test_bad_constraint():
    with pytest.raises(blazon.helpers.ConstraintKeyError):

        class Person(Schematic):
            name: str
            age: int = field(default=42, broken=1)


def test_from_file():
    class Person(Schematic):
        __schema__ = json.from_file(
            os.path.join(os.path.dirname(__file__), "schemas", "Person.yaml")
        )


def test_subclass():
    class Person(Schematic):
        name: str
        age: int = field(default=42, minimum=0)

    class Human(Person):
        pronoun: str

    sam = Human(name="Sam", pronoun="them")
    assert sam.validate()


def test_abstract_subclass():
    class Entity(Schematic):
        def hello(self):
            return "Hello %s" % self

    class Person(Entity):
        name: str = field(repr=True)
        age: int = field(default=42, minimum=0)

    beatrice = Person(name="Beatrice")
    assert beatrice.validate()

    assert beatrice.hello() == "Hello Person(name='Beatrice')"
