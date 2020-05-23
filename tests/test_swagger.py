import os, pytest, yaml
import blazon

from blazon import Schematic, json


def test_from_file():
    class Swagger(Schematic):
        __schema__ = json.from_file(
            os.path.join(os.path.dirname(__file__), "schemas", "swagger.yaml"), name="Swagger"
        )

    s = Swagger()
    assert not s.validate()

    assert Swagger.__schema__({"openapi": "3.0.0"}, partial=True)

    s.info = {"title": "Swagger Petstore", "version": "0.0.1"}
    s.openapi = "3.0.0"
    s.paths = []

    assert s.validate()

    petstore_path = os.path.join(os.path.dirname(__file__), "data", "petstore.yaml")
    with open(petstore_path) as o:
        data = yaml.safe_load(o)

    petstore = Swagger(**data)

    assert petstore.info["title"] == "Swagger Petstore"
    assert petstore.validate()

    old_value = petstore.get_value()

    class Info(Schematic):
        __schema__ = json.schemas["Info"]

    petstore.info = Info(title="Swagger Petstore", version="0.0.1")

    # Still validates
    assert petstore.validate()

    # .info is now an Info object
    assert isinstance(petstore.info, Info)

    # Now we access it with dots because info isn't a dict, it's an Info Schematic
    assert petstore.info.version == "0.0.1"

    # Still the same 'value' as before
    assert old_value == petstore.get_value()

    # We can assign it as a dict, shows up as Info object
    petstore.info = {"title": "Swagger Petstore", "version": "0.0.1"}
    assert old_value == petstore.get_value()
    assert isinstance(petstore.info, Info)
