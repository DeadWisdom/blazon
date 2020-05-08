import blazon


def test_items():
    # List
    s = blazon.schema({"items": {"const": 5}})

    assert s.validate([5])
    assert s.validate([5, 5, 5, 5])
    assert not s.validate([1])
    assert not s.validate([5, 5, 5, 1])

    # Tuple
    s = blazon.schema({"items": ({"const": 1}, {"const": 2}, {"const": 3})})
    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 4, 5])
    assert not s.validate([1])
    assert not s.validate([1, 2])
    assert not s.validate([])


def test_additional_items():
    s = blazon.schema(
        {"items": [{"const": 1}, {"const": 2}, {"const": 3}], "additional-items": {"const": 0}}
    )

    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 0, 0])
    assert not s.validate([1, 2, 3, 4, 5])

    s = blazon.schema(
        {"items": [{"const": 1}, {"const": 2}, {"const": 3}], "additional-items": False}
    )

    assert s.validate([1, 2, 3])
    assert not s.validate([1, 2, 3, 0, 0])


def test_max_items():
    s = blazon.schema({"maxItems": 3})

    assert s.validate([])
    assert s.validate([1, 2, 3])
    assert not s.validate([1, 2, 3, 4, 5])

    assert s([1, 2, 3, 4, 5]) == [1, 2, 3]


def test_min_items():
    s = blazon.schema({"minItems": 3})

    assert not s.validate([])
    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 4, 5])


def test_uniqueness():
    s = blazon.schema({"uniqueItems": True})

    assert s.validate([1, 2, 3])
    assert s.validate([])
    assert not s.validate([2, 2])
    assert not s.validate([1, 2, 3, 1])

    assert s([1, 2, 3, 1]) == {1, 2, 3}


def test_contains():
    s = blazon.schema({"contains": {"const": 1}})

    assert s.validate([1, 2, 3])
    assert s.validate([1, 1, 1])
    assert not s.validate([])
    assert not s.validate([2, 3, 4])
