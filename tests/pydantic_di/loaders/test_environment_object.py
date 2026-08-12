import os
from typing import Annotated, Literal
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Discriminator

from pydantic_di.loaders.environment_object import ObjectLoaderEnvironment


# --- Sample discriminated-subtype models for testing ---
class DummyStoreA(BaseModel):
    type: Literal["A"] = "A"
    foo: str = "default_foo"
    num: int = 1


class DummyStoreB(BaseModel):
    type: Literal["B"] = "B"
    bar: str
    flag: bool = False


LoaderUnion = Annotated[DummyStoreA | DummyStoreB, Discriminator("type")]


@pytest.mark.parametrize(
    "env_overrides, expected_values, expected_instance",
    [
        (
            {
                "DUMMY_STORE_TYPE": "A",
                "DUMMY_STORE_A_FOO": "hello_world",
                "DUMMY_STORE_A_NUM": "42",
            },
            {"type": "A", "foo": "hello_world", "num": "42"},
            DummyStoreA(foo="hello_world", num=42),
        ),
        (
            {
                "DUMMY_STORE_TYPE": "B",
                "DUMMY_STORE_B_BAR": "hello_world",
                "DUMMY_STORE_B_FLAG": "True",
            },
            {"type": "B", "bar": "hello_world", "flag": "True"},
            DummyStoreB(bar="hello_world", flag=True),
        ),
    ],
)
def test_loader_multi_type(env_overrides, expected_values, expected_instance):
    """Selects correct subtype and applies field overrides from env vars."""
    loader = ObjectLoaderEnvironment[LoaderUnion]()

    with patch.dict(os.environ, env_overrides, clear=False):
        result = loader.load()
        assert result == expected_instance


@pytest.mark.parametrize(
    "env_overrides, expected_values, expected_instance",
    [
        (
            {
                "DUMMY_STORE_A_FOO": "hello_world",
                "DUMMY_STORE_A_NUM": "42",
            },
            {"foo": "hello_world", "num": "42"},
            DummyStoreA(foo="hello_world", num=42),
        ),
    ],
)
def test_loader_single_type(env_overrides, expected_values, expected_instance):
    loader = ObjectLoaderEnvironment[DummyStoreA]()

    with patch.dict(os.environ, env_overrides, clear=False):
        result = loader.load()
        assert result == expected_instance


class Credentials(BaseModel):
    username: str
    password: str


class ServiceConfig(BaseModel):
    api_key: str
    port: int
    credentials: Credentials


def test_loader_object_default_values_env_wins_after_alignment():
    loader = ObjectLoaderEnvironment[ServiceConfig](
        env_prefix="MY_CONFIG",
        default_values={
            "api_key": "default",
            "port": 5432,
            "credentials": {
                "username": "admin",
                "password": "secret",
            },
        },
    )

    env_overrides = {
        "MY_CONFIG_API_KEY": "configured",
        "MY_CONFIG_PORT": "6432",
        "MY_CONFIG_CREDENTIALS_USERNAME": "matt",
    }

    with patch.dict(os.environ, env_overrides, clear=False):
        result = loader.load()

    assert result == ServiceConfig(
        api_key="configured",
        port=6432,
        credentials=Credentials(
            username="matt",
            password="secret",
        ),
    )


def test_loader_object_default_values_used_when_no_env_data():
    loader = ObjectLoaderEnvironment[ServiceConfig](
        env_prefix="MY_CONFIG",
        default_values={
            "api_key": "default",
            "port": 5432,
            "credentials": {
                "username": "admin",
                "password": "secret",
            },
        },
    )

    with patch.dict(os.environ, {}, clear=True):
        result = loader.load()

    assert result == ServiceConfig(
        api_key="default",
        port=5432,
        credentials=Credentials(
            username="admin",
            password="secret",
        ),
    )
