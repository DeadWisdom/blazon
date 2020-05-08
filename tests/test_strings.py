import pytest
import blazon

### String Types ###
def test_max_length():
    s = blazon.schema({"max-length": 5})

    assert s.validate("foo")
    assert s.validate("foob")
    assert s.validate("fooba")
    assert not s.validate("foobar")

    assert s("foobar") == "fooba"


def test_min_length():
    s = blazon.schema({"min-length": 5})

    assert s.validate("foobarfoobarfoobar")
    assert s.validate("foobar")
    assert not s.validate("foo")
    assert not s.validate("")

    with pytest.raises(blazon.ValidationError):
        assert s("foo")


def test_pattern():
    s = blazon.schema({"pattern": "^(\\([0-9]{3}\\))?[0-9]{3}-[0-9]{4}$"})

    assert s.validate("555-1212")
    assert s.validate("(888)555-1212")
    assert not s.validate("(888)555-1212 ext. 532")
    assert not s.validate("(800)FLOWERS")
    assert not s.validate("None")

    s = blazon.schema({"pattern": "ob"})

    assert s.validate("foobar")
    assert not s.validate("--")
