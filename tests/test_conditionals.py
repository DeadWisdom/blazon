import blazon


def test_if_then_else():
    s = blazon.schema(
        {"if": {"maximum": 4}, "then": {"multiple-of": 2}, "else": {"multiple-of": 3},}
    )

    assert not s.validate(1)
    assert s.validate(2)
    assert not s.validate(3)
    assert s.validate(4)
    assert not s.validate(5)
    assert s.validate(6)
    assert not s.validate(7)
    assert not s.validate(8)
    assert s.validate(9)
    assert not s.validate(10)
    assert s.validate(12)


def test_all_of():
    s = blazon.schema({"allOf": [{"type": str, "max_length": 6}, {"type": str, "min_length": 3}]})

    assert not s.validate("")
    assert s.validate("foo")
    assert s.validate("foobar")
    assert not s.validate("foobarbar")

    s = blazon.schema({"allOf": [{"type": str, "max_length": 3}, {"type": int, "maximum": 5}]})

    assert s("666---") == 5


def test_any_of():
    s = blazon.schema({"anyOf": [{"type": int, "maximum": 4}, {"type": int, "multiple-of": 4}]})

    assert s.validate(1)
    assert s.validate(2)
    assert s.validate(4)
    assert not s.validate(5)
    assert s.validate(8)
    assert not s.validate(10)

    s = blazon.schema({"anyOf": [{"type": int, "maximum": 4}, {"type": str}]})

    assert s.validate("asdf")
    assert s.validate(4)

    assert s("asdf") == "asdf"
    assert s(10) == 4


def test_one_of():
    s = blazon.schema({"oneOf": [{"type": int, "maximum": 4}, {"type": int, "multiple-of": 4}]})

    assert s.validate(1)
    assert s.validate(2)
    assert not s.validate(4)
    assert not s.validate(5)
    assert s.validate(8)
    assert not s.validate(10)


def test_not():
    s = blazon.schema({"not": {"type": int}})

    assert s.validate("foo")
    assert not s.validate(2)
