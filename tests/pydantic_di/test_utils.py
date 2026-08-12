import pytest
from pydantic import BaseModel

from pydantic_di.utils import deep_merge, to_env_prefix, type_name_intersection


class DummyStoreA(BaseModel): ...


class OtherThing(BaseModel): ...


class DummyStorage(BaseModel): ...


class DummyStoreB(BaseModel): ...


class StartMiddleEnd(BaseModel): ...


class MiddleEndFinal(BaseModel): ...


class RandomEnd(BaseModel): ...


class XabcY(BaseModel): ...


class ZabcW(BaseModel): ...


class JustC(BaseModel): ...


class StartsWithZ(BaseModel): ...


class EndsWithZ(BaseModel): ...


@pytest.mark.parametrize(
    "types,expected_prefix",
    [
        ((StartMiddleEnd, MiddleEndFinal), "MiddleEnd"),  # overlap in the middle and end
        ((StartMiddleEnd, RandomEnd), "End"),  # shared suffix only
        ((XabcY, ZabcW), "abc"),  # overlap in the middle
        ((JustC, XabcY, ZabcW), ""),  # only 'c' is shared across all
        ((StartsWithZ, EndsWithZ), "sWithZ"),  # overlap only at opposite ends
        ((DummyStoreA, OtherThing), "t"),  # still just 'o'
        ((DummyStoreA, DummyStorage, DummyStoreB), "DummyStor"),
        ((DummyStoreA,), "DummyStoreA"),
        ((), ""),
    ],
)
def test_type_name_intersection(types, expected_prefix):
    assert type_name_intersection(types) == expected_prefix


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("OAuth2TokenStore", "O_AUTH2_TOKEN_STORE"),
        ("XMLParser", "XML_PARSER"),
        ("MySuperClass", "MY_SUPER_CLASS"),
        ("simpleClass", "SIMPLE_CLASS"),
        ("HTTPServerResponse", "HTTP_SERVER_RESPONSE"),
        ("", ""),
    ],
)
def test_to_env_prefix(input_name, expected):
    assert to_env_prefix(input_name) == expected


def test_deep_merge_configured_wins_recursively_and_inputs_unchanged():
    defaults = {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "admin",
            "password": "secret",
        },
    }
    configured = {
        "port": "6432",
        "credentials": {
            "username": "matt",
        },
    }

    merged = deep_merge(defaults, configured)

    assert merged == {
        "host": "localhost",
        "port": "6432",
        "credentials": {
            "username": "matt",
            "password": "secret",
        },
    }

    # Ensure helper does not mutate either input.
    assert defaults == {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "admin",
            "password": "secret",
        },
    }
    assert configured == {
        "port": "6432",
        "credentials": {
            "username": "matt",
        },
    }


def test_deep_merge_non_dict_configured_replaces_dict_default():
    merged = deep_merge(
        {
            "service": {
                "host": "localhost",
            },
        },
        {
            "service": "disabled",
        },
    )

    assert merged == {
        "service": "disabled",
    }
