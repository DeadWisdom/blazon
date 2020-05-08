import pytest
import blazon


def test_format_toggle():
    env = blazon.native
    s = env.schema({"type": str, "format": "datetime"})

    env.ignore_formats = True
    s.compile()
    assert s.validate("not a time")

    env.ignore_formats = False
    s.compile()
    assert not s.validate("not a time")

    env.ignore_these_formats = ["date_time"]
    s.compile()
    assert s.validate("not a time")

    env.ignore_these_formats = []
    s.compile()
    assert not s.validate("not a time")


def test_format_date_time():
    s = blazon.schema({"type": str, "format": "datetime"})

    assert s.validate("1980-06-16T10:15:23-04:00")
    assert s.validate("1980-06-16T14:15:23Z")


def test_format_date():
    s = blazon.schema({"type": str, "format": "date"})

    assert s.validate("1980-06-16")


def test_format_time():
    s = blazon.schema({"type": str, "format": "time"})

    assert s.validate("10:15:23-04:00")
    assert s.validate("14:15:23Z")


def test_email():
    s = blazon.schema({"type": str, "format": "email"})

    assert s.validate("brantley@example.com")
    assert not s.validate("a@a")
    assert not s.validate("--")


def test_hostname():
    s = blazon.schema({"type": str, "format": "hostname"})

    assert s.validate("www.example.com")
    assert s.validate("forge.works")
    assert not s.validate("--")
    assert not s.validate("/hello/")


def test_ip_addresses():
    s = blazon.schema({"type": str, "format": "ipv4"})

    assert s.validate("127.0.0.1")
    assert not s.validate("277.0.0.1")
    assert not s.validate("-")

    s = blazon.schema({"type": str, "format": "ipv6"})

    assert s.validate("2001:db8::")
    assert s.validate("2001:DB8:0:0:8:800:200C:417A")
    assert s.validate("FF01:0:0:0:0:0:0:101")
    assert s.validate("0:0:0:0:0:0:0:0")
    assert s.validate("0:0:0:0:0:0:0:1")
    assert s.validate("::")
    assert not s.validate("-")
    assert not s.validate("1200::AB00:1234::2552:7777:1313")


def test_uri():
    # Skip this test if we don't have the rfc module.
    pytest.importorskip("rfc3987")

    s = blazon.schema({"type": str, "format": "uri"})

    assert s.validate("http://tools.ietf.org/html/rfc3986#appendix-A")
    assert not s.validate("antidisestablishmentarianism")

    s = blazon.schema({"type": str, "format": "uri-reference"})

    assert s.validate("urn:place/sub")


def test_iri():
    # Skip this test if we don't have the rfc module.
    pytest.importorskip("rfc3987")

    s = blazon.schema({"type": str, "format": "iri"})

    assert s.validate("http://tools.ietf.org/html/rfc3986#appendix-A")
    assert not s.validate("antidisestablishmentarianism")

    s = blazon.schema({"type": str, "format": "iri-reference"})

    assert s.validate("urn:place/sub")
