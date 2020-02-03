import pytest

from blazon.json_schema import system as json
from blazon.helpers import ValidationError

EMPTY = json.schema({})


### Test Registration ###
def test_constraint_names():
    assert 'multipleOf' in json.constraints


### All Primitive Types ###
def test_type():
    s = json.schema({
        'type': 'integer'
    })
    assert s.validate(10)
    assert not s.validate('10')
    assert s(10) == 10
    assert s('10') == 10

    s = json.schema({
        'type': 'string'
    })
    assert not s.validate(10)
    assert s.validate('10')
    assert s(10) == '10'
    assert s('10') == '10'


def test_enum():
    s = json.schema({
        'enum': ['bob', 'carol', 'jane']
    })

    assert s.validate('bob')
    assert s.validate('carol')
    assert s.validate('jane')
    assert not s.validate('asdfasf')
    assert not s.validate(None)

    with pytest.raises(ValidationError):
        s(None)


def test_const():
    s = json.schema({
        'const': 5
    })

    assert s.validate(5)
    assert not s.validate(4)

    assert s(1) == 5

    s = json.schema({
        'const': 'jane'
    })

    assert s.validate('jane')
    assert not s.validate('bob')

    assert s('bob') == 'jane'


### Numeric Types ###
def test_muiltiple_of():
    s = json.schema({
        'multiple-of': 2
    })

    assert s.validate(4)
    assert s.validate(2)
    assert not s.validate(3)
    assert not s.validate(1)

    with pytest.raises(ValidationError):
        s(5)

    s = json.schema({
        'multiple-of': 1.5
    })
    assert s.validate(3)
    assert not s.validate(4)


def test_maximum():
    s = json.schema({
        'maximum': 5
    })

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
    s._set_constraint('exclusive_maximum', True)
    assert not s.validate(5)
    with pytest.raises(ValidationError):
        assert s(10)
    s._set_constraint('exclusive_maximum', False)
    assert s.validate(5)
    assert s(10) == 5
    s._del_constraint('exclusive_maximum')
    assert s.validate(5)
    assert s(10) == 5

    # Exclusive maximum validates whatever
    s = json.schema({
        'exclusive-maximum': True
    })

    assert s.validate(4)
    assert s.validate(None)


def test_minimum():
    s = json.schema({
        'minimum': 0
    })

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
    s._set_constraint('exclusive_minimum', True)
    assert s(10) == 10
    with pytest.raises(ValidationError):
        assert s(-10)
    s._set_constraint('exclusive_minimum', False)
    assert s.validate(0)
    assert s(-10) == 0
    s._del_constraint('exclusive_minimum')
    assert s.validate(0)
    assert s(-10) == 0

    # Exclusive minimum validates whatever
    s = json.schema({
        'exclusive-minimum': True
    })
    assert s.validate(5)
    assert s.validate(None)


### String Types ###
def test_max_length():
    s = json.schema({
        'max-length': 5
    })

    assert s.validate("foo")
    assert s.validate("foob")
    assert s.validate("fooba")
    assert not s.validate("foobar")

    assert s('foobar') == 'fooba'


def test_min_length():
    s = json.schema({
        'min-length': 5
    })

    assert s.validate("foobarfoobarfoobar")
    assert s.validate("foobar")
    assert not s.validate("foo")
    assert not s.validate("")

    with pytest.raises(ValidationError):
        assert s('foo')


def test_pattern():
    s = json.schema({
        'pattern': "^(\\([0-9]{3}\\))?[0-9]{3}-[0-9]{4}$"
    })

    assert s.validate("555-1212")
    assert s.validate("(888)555-1212")
    assert not s.validate("(888)555-1212 ext. 532")
    assert not s.validate("(800)FLOWERS")
    assert not s.validate("None")

    s = json.schema({
        'pattern': "ob"
    })

    assert s.validate("foobar")
    assert not s.validate("--")


### Array Types ###
def test_items():
    # List
    s = json.schema({
        'items': {'const': 5}
    })

    assert s.validate([5])
    assert s.validate([5, 5, 5, 5])
    assert not s.validate([1])
    assert not s.validate([5, 5, 5, 1])

    # Tuple
    s = json.schema({
        'items': ({'const': 1}, {'const': 2}, {'const': 3})
    })
    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 4, 5])
    assert not s.validate([1])
    assert not s.validate([1, 2])
    assert not s.validate([])


def test_additional_items():
    s = json.schema({
        'items': [{'const': 1}, {'const': 2}, {'const': 3}],
        'additionalItems': {'const': 0}
    })

    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 0, 0])
    assert not s.validate([1, 2, 3, 4, 5])

    s = json.schema({
        'items': [{'const': 1}, {'const': 2}, {'const': 3}],
        'additional-items': False
    })

    assert s.validate([1, 2, 3])
    assert not s.validate([1, 2, 3, 0, 0])


def test_max_items():
    s = json.schema({
        'maxItems': 3
    })

    assert s.validate([])
    assert s.validate([1, 2, 3])
    assert not s.validate([1, 2, 3, 4, 5])

    assert s([1, 2, 3, 4, 5]) == [1, 2, 3]


def test_min_items():
    s = json.schema({
        'minItems': 3
    })

    assert not s.validate([])
    assert s.validate([1, 2, 3])
    assert s.validate([1, 2, 3, 4, 5])


def test_uniqueness():
    s = json.schema({
        'uniqueItems': True
    })

    assert s.validate([1, 2, 3])
    assert s.validate([])
    assert not s.validate([2, 2])
    assert not s.validate([1, 2, 3, 1])

    assert s([1, 2, 3, 1]) == [1, 2, 3]


def test_contains():
    s = json.schema({
        'contains': {'const': 1}
    })

    assert s.validate([1, 2, 3])
    assert s.validate([1, 1, 1])
    assert not s.validate([])
    assert not s.validate([2, 3, 4])


### Object ###
def test_max_properties():
    s = json.schema({
        'maxProperties': 2
    })

    assert s.validate({})
    assert s.validate({'a': 1})
    assert s.validate({'a': 1, 'b': 2})
    assert not s.validate({'a': 1, 'b': 2, 'c': 3})


def test_min_properties():
    s = json.schema({
        'minProperties': 2
    })

    assert not s.validate({})
    assert not s.validate({'a': 1})
    assert s.validate({'a': 1, 'b': 2})
    assert s.validate({'a': 1, 'b': 2, 'c': 3})


def test_required():
    s = json.schema({
        'required': ['a', 'b']
    })

    assert s.validate({'a': 1, 'b': 2, 'c': 3})
    assert s.validate({'a': 1, 'b': 2})
    assert not s.validate({'a': 1})
    assert not s.validate({})


def test_properties():
    s = json.schema({
        'properties': {
            'name': {'type': 'string', 'min_length': 3},
            'age': {'type': 'integer', 'minimum': 18, 'maximum': 130},
        }
    })

    assert s.validate({'name': 'bob', 'age': 41})
    assert s.validate({'name': 'bob', 'age': 41, 'other': 2})

    assert not s.validate({'name': 'bob', 'age': 400})
    assert not s.validate({'name': '?', 'age': 14})
    
    # Missing properties are ignored
    assert s.validate({})


def test_pattern_properties():
    s = json.schema({
        'patternProperties': {
            'name': {'type': 'string', 'min_length': 3},
            'review-(\d+)': {'type': 'integer', 'minimum': 0, 'maximum': 5},
        }
    })

    assert s.validate({'name': 'carol', 'review-1': 4, 'review-2': 3, 'review': 50, 'review-extra': -40})
    assert not s.validate({'name': 'carol', 'review-1': 10})


def test_additional_properties():
    s = json.schema({
        'properties': {'name': {'type': 'string'}},
        'patternProperties': {'review-(\d+)': {'type': 'integer'}},
        'additionalProperties': {'type': 'array'},
    })

    assert s.validate({'name': 'carol', 'review-1': 4, 'review-2': 3})
    assert s.validate({'name': 'carol', 'review-1': 4, 'review-2': 3, 'additional': [1, 2, 3]})
    assert not s.validate({'name': 'carol', 'review-1': 4, 'review-2': 3, 'additional': 4})


def test_dependencies():
    s = json.schema({
        'dependencies': {'credit_card': ['billing_address']}
    })

    assert s.validate({})
    assert s.validate({'billing_address': '42 Main St'})
    assert not s.validate({'credit_card': '4141-414141-414141'})
    assert s.validate({'credit_card': '4141-414141-414141', 'billing_address': '42 Main St'})

    s = json.schema({
        'dependencies': {
            'credit_card': {
                'required': ['billing_address'],
                'properties': {
                    'billing_address': {'type': 'string'}
                }
            }
        }
    })

    assert s.validate({})
    assert s.validate({'billing_address': '42 Main St'})
    assert not s.validate({'credit_card': '4141-414141-414141'})
    assert s.validate({'credit_card': '4141-414141-414141', 'billing_address': '42 Main St'})
    assert not s.validate({'credit_card': '4141-414141-414141', 'billing_address': ['bob']})


def test_property_names():
    s = json.schema({
        'propertyNames': {'type': 'string', 'min_length': 3},
    })

    assert s.validate({})
    assert s.validate({'foo': 1})
    assert s.validate({'foo': 1, 'foobar': 2})
    assert not s.validate({'foo': 1, 'foobar': 2, 'x': 3})
    assert not s.validate({'x': 3})


### Conditionals ###
def test_if_then_else():
    s = json.schema({
        'if': {'maximum': 4},
        'then': {'multiple-of': 2},
        'else': {'multiple-of': 3},
    })

    assert not s.validate(1)
    assert s.validate(2)
    assert not s.validate(3)
    assert s.validate(4)
    assert not s.validate(5)
    assert s.validate(6)
    assert not s.validate(7)
    assert s.validate(8)
    assert not s.validate(9)
    assert s.validate(10)
    assert s.validate(12)


def test_all_of():
    s = json.schema({
        'allOf': [{'type': 'string', 'max_length': 6}, {'type': 'string', 'min_length': 3}]
    })
    
    assert not s.validate('')
    assert s.validate('foo')
    assert s.validate('foobar')
    assert not s.validate('foobarbar')

    s = json.schema({
        'allOf': [{'type': 'string', 'max_length': 3}, {'type': 'integer', 'maximum': 5}]
    })

    assert s('666---') == 5


def test_any_of():
    s = json.schema({
        'anyOf': [{'type': 'integer', 'maximum': 4}, {'type': 'integer', 'multiple-of': 4}]
    })

    assert s.validate(1)
    assert s.validate(2)
    assert s.validate(4)
    assert not s.validate(5)
    assert s.validate(8)
    assert not s.validate(10)

    s = json.schema({
        'anyOf': [{'type': 'integer', 'maximum': 4}, {'type': 'string'}]
    })

    assert s.validate("asdf")
    assert s.validate(4)

    assert s("asdf") == "asdf"
    assert s(10) == 4
    

def test_one_of():
    s = json.schema({
        'oneOf': [{'type': 'integer', 'maximum': 4}, {'type': 'integer', 'multiple-of': 4}]
    })

    assert s.validate(1)
    assert s.validate(2)
    assert not s.validate(4)
    assert not s.validate(5)
    assert s.validate(8)
    assert not s.validate(10)


def test_not():
    s = json.schema({
        'not': {'type': 'integer'}
    })

    assert s.validate('foo')
    assert not s.validate(2)


### Format ###
def test_format_toggle():
    s = json.schema({'type': 'string', 'format': 'datetime'})
    
    json.ignore_all_formats = True
    assert s.validate("not a time")

    json.ignore_all_formats = False
    assert not s.validate("not a time")

    json.ignore_these_formats = ['dateTime']
    assert s.validate("not a time")

    json.ignore_these_formats = [] 
    assert not s.validate("not a time")

def test_format_date_time():
    s = json.schema({'type': 'string', 'format': 'datetime'})

    assert s.validate("1980-06-16T10:15:23-04:00")
    assert s.validate("1980-06-16T14:15:23Z")

def test_format_date():
    s = json.schema({'type': 'string', 'format': 'date'})

    assert s.validate("1980-06-16")

def test_format_time():
    s = json.schema({'type': 'string', 'format': 'time'})

    assert s.validate("10:15:23-04:00")
    assert s.validate("14:15:23Z")

def test_email():
    s = json.schema({'type': 'string', 'format': 'email'})

    assert s.validate("brantley@example.com")
    assert not s.validate("a@a")
    assert not s.validate("--")

def test_hostname():
    s = json.schema({'type': 'string', 'format': 'hostname'})

    assert s.validate("www.example.com")
    assert s.validate("forge.works")
    assert not s.validate("--")
    assert not s.validate("/hello/")

def test_ip_addresses():
    s = json.schema({'type': 'string', 'format': 'ipv4'})

    assert s.validate("127.0.0.1")
    assert not s.validate("277.0.0.1")
    assert not s.validate("-")

    s = json.schema({'type': 'string', 'format': 'ipv6'})

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
    pytest.importorskip('rfc3987')  

    s = json.schema({'type': 'string', 'format': 'uri'})

    assert s.validate("http://tools.ietf.org/html/rfc3986#appendix-A")
    assert not s.validate("antidisestablishmentarianism")

    s = json.schema({'type': 'string', 'format': 'uri-reference'})

    assert s.validate("urn:place/sub")

def test_iri():
    # Skip this test if we don't have the rfc module.
    pytest.importorskip('rfc3987')  

    s = json.schema({'type': 'string', 'format': 'iri'})

    assert s.validate("http://tools.ietf.org/html/rfc3986#appendix-A")
    assert not s.validate("antidisestablishmentarianism")

    s = json.schema({'type': 'string', 'format': 'iri-reference'})

    assert s.validate("urn:place/sub")


### Meta ###
def test_value():
    s = json.schema({'type': 'string', 'format': 'email', 'min_length': 8})

    assert s.value == {
        'type': 'string',
        'format': 'email',
        'minLength': 8
    }

    s = json.schema({'type': 'array', 'items': {'type': 'string'}})

    assert s.value == {
        'type': 'array',
        'items': {
            'type': 'string'
        }
    }

    assert s.value == json.schema(s.value).value


### Test Errors ###
def test_wrong_primitive():
  with pytest.raises(ValueError):
    json.schema({'type': 'wrong'})