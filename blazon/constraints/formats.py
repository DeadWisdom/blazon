import logging
from inflection import underscore
from functools import wraps
from typing import Callable, Set, Any
from .base import Constraint, ConstraintFailure, register, Undefined


format_registry = {}


def add_format(name, fn):
    format_registry[underscore(name)] = fn


def get_format(name):
    return format_registry.get(underscore(name))


def format(fn):
    add_format(fn.__name__, fn)
    return fn


@register(name="format", description="String must match a certain format", require=[str])
def format_constraint(schema, value):
    if schema.env.ignore_formats:
        return

    # Datetime alias
    if value == "datetime":
        value = "date_time"

    if schema.env.inflection(value) in schema.env.ignore_these_formats:
        return

    fn = get_format(value)

    if fn is None and schema.strict:
        raise NameError(f"Cannot find format: {value!r}")

    def handler(instance, convert=False, partial=False):
        if not fn(instance):
            raise ConstraintFailure(f"{instance!r} does not match the format: {value!r}")
        return instance

    return handler


### Formats ###
import re
import ipaddress

date_re = re.compile(r"^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$")
time_re = re.compile(r"^\s*(\d\d):(\d\d):(\d\d)(\.(\d+))?([zZ]|(([-+])(\d\d):?(\d\d)))\s*$")
date_time_re = re.compile(
    r"^\s*(\d\d\d\d)-(\d\d)-(\d\d)[ tT](\d\d):(\d\d):(\d\d)(\.(\d+))?([zZ]|(([-+])(\d\d):?(\d\d)))\s*$"
)
email_re = re.compile(
    r'(?:[a-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'
)
hostname_re = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)


@format
def date_time(instance):
    return date_time_re.match(instance) is not None


@format
def date(instance):
    return date_re.match(instance) is not None


@format
def time(instance):
    return time_re.match(instance) is not None


@format
def email(instance):
    return email_re.match(instance) is not None


@format
def hostname(instance):
    if len(instance) > 255:
        return False
    if instance[-1] == ".":
        instance = instance[:-1]
    return all(hostname_re.match(x) for x in instance.split("."))


@format
def ipv4(instance):
    try:
        ipaddress.IPv4Address(instance)
        return True
    except ValueError:
        return False


@format
def ipv6(instance):
    try:
        ipaddress.IPv6Address(instance)
        return True
    except ValueError:
        return False


@format
def uri(instance):
    try:
        import rfc3987
    except ImportError:
        logging.warning("package rfc3987 missing - cannot validate uri - so it passes")
        return True
    return rfc3987.match(instance, rule="URI")


@format
def uri_reference(instance):
    try:
        import rfc3987
    except ImportError:
        logging.warning("package rfc3987 missing - cannot validate uri-reference - so it passes")
        return True
    return rfc3987.match(instance, rule="URI_reference")


@format
def iri(instance):
    try:
        import rfc3987
    except ImportError:
        logging.warning("package rfc3987 missing - cannot validate iri - so it passes")
        return True
    return rfc3987.match(instance, rule="IRI")


@format
def iri_reference(instance):
    try:
        import rfc3987
    except ImportError:
        logging.warning("package rfc3987 missing - cannot validate iri-reference - so it passes")
        return True
    return rfc3987.match(instance, rule="IRI_reference")
