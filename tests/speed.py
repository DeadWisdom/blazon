import pytest
import fastjsonschema
import jsonschema
from blazon import json


@pytest.fixture
def user_bob():
    return {"name": "Bob", "tags": ["1", "2", "3"]}


@pytest.fixture
def user_drew():
    return {"name": "Drew", "age": 67, "tags": []}


@pytest.fixture
def user_schema():
    return {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number", "default": 42},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
    }


def test_blazon_bob(benchmark, user_schema, user_bob):
    splendid = json.schema(user_schema)

    @benchmark
    def blazon():
        splendid.validate(user_bob)


def test_convert_blazon_bob(benchmark, user_schema, user_bob):
    splendid = json.schema(user_schema)

    @benchmark
    def blazon():
        splendid(user_bob)


def test_slow_blazon_bob(benchmark, user_schema, user_bob):
    @benchmark
    def blazon():
        json.schema(user_schema).validate(user_bob)


def test_slow_fast_bob(benchmark, user_schema, user_bob):
    @benchmark
    def fast():
        fastjsonschema.validate(user_schema, user_bob)


def test_fast_bob(benchmark, user_schema, user_bob):
    fast = fastjsonschema.compile(user_schema)

    @benchmark
    def fast():
        fast(user_bob)


def test_jsonschema_bob(benchmark, user_schema, user_bob):
    @benchmark
    def json():
        jsonschema.validate(user_schema, user_bob)


def test_blazon_drew(benchmark, user_schema, user_drew):
    splendid = json.schema(user_schema)

    @benchmark
    def blazon():
        splendid.validate(user_drew)


def test_convert_blazon_drew(benchmark, user_schema, user_drew):
    splendid = json.schema(user_schema)

    @benchmark
    def blazon():
        splendid(user_drew)


def test_slow_blazon_drew(benchmark, user_schema, user_drew):
    @benchmark
    def blazon():
        json.schema(user_schema).validate(user_drew)


def test_slow_fast_drew(benchmark, user_schema, user_drew):
    @benchmark
    def fast():
        fastjsonschema.validate(user_schema, user_drew)


def test_fast_drew(benchmark, user_schema, user_drew):
    fast = fastjsonschema.compile(user_schema)

    @benchmark
    def fast():
        fast(user_drew)


def test_jsonschema_drew(benchmark, user_schema, user_drew):
    @benchmark
    def json():
        jsonschema.validate(user_schema, user_drew)
