import blazon


def test_max_entries():
    s = blazon.schema({"max-entries": 2})

    assert s.validate({})
    assert s.validate({"a": 1})
    assert s.validate({"a": 1, "b": 2})
    assert not s.validate({"a": 1, "b": 2, "c": 3})


def test_min_entries():
    s = blazon.schema({"min-entries": 2})

    assert not s.validate({})
    assert not s.validate({"a": 1})
    assert s.validate({"a": 1, "b": 2})
    assert s.validate({"a": 1, "b": 2, "c": 3})


def test_required():
    s = blazon.schema({"required": ["a", "b"]})

    assert s.validate({"a": 1, "b": 2, "c": 3})
    assert s.validate({"a": 1, "b": 2})
    assert not s.validate({"a": 1})
    assert not s.validate({})


def test_entries():
    s = blazon.schema(
        {
            "entries": {
                "name": {"type": str, "min_length": 3},
                "age": {"type": int, "minimum": 18, "maximum": 130},
            }
        }
    )

    assert s.validate({"name": "bob", "age": 41})
    assert s.validate({"name": "bob", "age": 41, "other": 2})

    assert not s.validate({"name": "bob", "age": 400})
    assert not s.validate({"name": "?", "age": 14})

    # Missing entries are ignored
    assert s.validate({})


def test_pattern_properties():
    s = blazon.schema(
        {
            "patternEntries": {
                "name": {"type": str, "min_length": 3},
                "review-(\d+)": {"type": int, "minimum": 0, "maximum": 5},
            }
        }
    )

    assert s.validate(
        {"name": "carol", "review-1": 4, "review-2": 3, "review": 50, "review-extra": -40}
    )
    assert not s.validate({"name": "carol", "review-1": 10})


def test_additional_properties():
    s = blazon.schema(
        {
            "entries": {"name": {"type": str}},
            "patternEntries": {"review-(\d+)": {"type": int}},
            "additionalEntries": {"type": list},
        }
    )

    assert s.validate({"name": "carol", "review-1": 4, "review-2": 3})
    assert s.validate({"name": "carol", "review-1": 4, "review-2": 3, "additional": [1, 2, 3]})
    assert not s.validate({"name": "carol", "review-1": 4, "review-2": 3, "additional": 4})


def test_dependencies():
    s = blazon.schema({"dependencies": {"credit_card": ["billing_address"]}})

    assert s.validate({})
    assert s.validate({"billing_address": "42 Main St"})
    assert not s.validate({"credit_card": "4141-414141-414141"})
    assert s.validate({"credit_card": "4141-414141-414141", "billing_address": "42 Main St"})

    s = blazon.schema(
        {
            "dependencies": {
                "credit_card": {
                    "entries": {"billing_address": {"type": str}},
                    "required": ["billing_address"],
                }
            }
        }
    )

    assert s.validate({})
    assert s.validate({"billing_address": "42 Main St"})
    assert not s.validate({"credit_card": "4141-414141-414141"})
    assert s.validate({"credit_card": "4141-414141-414141", "billing_address": "42 Main St"})
    assert not s.validate({"credit_card": "4141-414141-414141", "billing_address": ["bob"]})


def test_property_names():
    s = blazon.schema({"entryNames": {"type": str, "min_length": 3},})

    assert s.validate({})
    assert s.validate({"foo": 1})
    assert s.validate({"foo": 1, "foobar": 2})
    assert not s.validate({"foo": 1, "foobar": 2, "x": 3})
    assert not s.validate({"x": 3})
