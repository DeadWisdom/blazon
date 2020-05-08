import pytest
import blazon


def test_multiple_of():
    s = blazon.schema({"multiple-of": 2})

    assert s.validate(4)
    assert s.validate(2)
    assert not s.validate(3)
    assert not s.validate(1)

    with pytest.raises(blazon.ValidationError):
        s(5)

    s = blazon.schema({"multiple-of": 1.5})
    assert s.validate(3)
    assert not s.validate(4)


def test_maximum():
    s = blazon.schema({"maximum": 5})

    assert s.validate(-10)
    assert s.validate(0)
    assert s.validate(4)
    assert not s.validate(6)

    assert s(-10) == -10
    assert s(0) == 0
    assert s(4) == 4
    assert s(6) == 5

    # Exclusive maximum changes our validation
    assert s.validate(5)
    s.value["exclusive_maximum"] = True
    s.compile()
    assert not s.validate(5)
    with pytest.raises(blazon.ValidationError):
        assert s(10)
    s.value["exclusive_maximum"] = False
    s.compile()
    assert s.validate(5)
    assert s(10) == 5
    s.value.pop("exclusive_maximum", 0)
    s.compile()
    assert s.validate(5)
    assert s(10) == 5

    # Exclusive maximum validates whatever
    s = blazon.schema({"exclusive-maximum": True})

    assert s.validate(4)
    assert s.validate(None)


def test_minimum():
    s = blazon.schema({"minimum": 0})

    assert not s.validate(-10)
    assert not s.validate(-1)
    assert s.validate(0)
    assert s.validate(4)

    assert s(-10) == 0
    assert s(-1) == 0
    assert s(0) == 0
    assert s(4) == 4

    # Exclusive minimum changes our validation
    assert s.validate(0)
    s.value["exclusive_minimum"] = True
    s.compile()
    assert s(10) == 10
    with pytest.raises(blazon.ValidationError):
        assert s(-10)
    s.value["exclusive_minimum"] = False
    s.compile()
    assert s.validate(0)
    assert s(-10) == 0
    s.value.pop("exclusive_maximum", 0)
    s.compile()
    assert s.validate(0)
    assert s(-10) == 0

    # Exclusive minimum validates whatever
    s = blazon.schema({"exclusive-minimum": True})
    assert s.validate(5)
    assert s.validate(None)


def test_maximum_with_bad_input():
    s = blazon.schema({"type": int, "maximum": 4})

    assert not s.validate("asdf")
