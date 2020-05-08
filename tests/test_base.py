import pytest
import blazon

from blazon import ValidationError


def test_type():
    number = blazon.schema({"type": int})

    assert number.validate(1)
    assert not number.validate("1")

    assert number(1) == 1
    assert number("1") == 1

    with pytest.raises(ValueError):
        number("beatrice")

    class A:
        def __init__(self, index):
            self.index = int(index)

    a_type = blazon.schema({"type": A})
    a = A(1)

    assert a_type.validate(a)
    assert not a_type.validate(None)

    assert a_type(a) is a
    assert a_type(1).index == 1

    with pytest.raises(ValueError):
        a_type("beatrice")


def test_enum():
    s = blazon.schema({"enum": ["bob", "carol", "jane"]})

    assert s.validate("bob")
    assert s.validate("carol")
    assert s.validate("jane")
    assert not s.validate("asdfasf")
    assert not s.validate(None)

    with pytest.raises(ValidationError):
        s(None)


def test_const():
    s = blazon.schema({"const": 5})

    assert s.validate(5)
    assert not s.validate(4)

    assert s(1) == 5

    s = blazon.schema({"const": "jane"})

    assert s.validate("jane")
    assert not s.validate("bob")

    assert s("bob") == "jane"


def test_wrong_primitive():
    with pytest.raises(ValueError):
        blazon.schema({"type": "wrong"})
