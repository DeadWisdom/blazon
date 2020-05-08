import os, pytest
import blazon

from blazon import Schematic, field, json


old_from_file = json.from_file
def from_local_file(filename):
    path = os.path.join(os.path.dirname(__file__), "schemas", filename)
    return old_from_file(path)

json.from_file = from_local_file


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
        __schema__ = json.from_file("Person.yaml")


def test_readme_character():
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


def test_readme_monster():
    from blazon import Schematic, json

    class Monster(Schematic):
        __schema__ = json.from_file('Monster.yaml')

    kate_monster = Monster(name="Kate")
    assert kate_monster.level == 1
