import os
from blazon import json

### Helpers ###
old_from_file = json.from_file
def from_local_file(filename):
    path = os.path.join(os.path.dirname(__file__), "schemas", filename)
    return old_from_file(path)

json.from_file = from_local_file

_open = open
def open(filename):
    return _open(os.path.join(os.path.dirname(__file__), "data", filename))


### Tests ###
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


def test_json():
    import blazon, json

    with open("users.json") as o:
      user_data = json.load(o)

    user_schema = blazon.json.schema({
      'properties': {
        'name': {'type': 'string'},
        'email': {'type': 'string', 'format': 'email'},
        'age': {'type': 'number', 'minValue': 0, 'default': 42},
      },
      'required': ['name', 'email']
    })

    users = [user_schema(item) for item in user_data]

    assert all(x['name'] for x in users)
    assert all('@' in x['email'] for x in users)
    assert all(x['age'] >= 0 for x in users)

    user = user_schema({'name': 'Bob'})
