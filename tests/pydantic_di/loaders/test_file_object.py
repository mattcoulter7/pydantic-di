import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Discriminator

from pydantic_di.loaders import ObjectLoaderIni, ObjectLoaderJson, ObjectLoaderToml, ObjectLoaderYaml


class Credentials(BaseModel):
    username: str
    password: str


class ServiceConfig(BaseModel):
    host: str
    port: int
    credentials: Credentials


class DummyStoreA(BaseModel):
    type: Literal["A"] = "A"
    foo: str = "default_foo"
    num: int = 1


class DummyStoreB(BaseModel):
    type: Literal["B"] = "B"
    bar: str


RoleStore = Annotated[DummyStoreA | DummyStoreB, Discriminator("type")]


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def write_yaml(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        "\n".join(
            [
                f"host: {data['host']}",
                f"port: {data['port']}",
                "credentials:",
                f"  username: {data['credentials']['username']}",
                f"  password: {data['credentials']['password']}",
            ]
        ),
        encoding="utf-8",
    )


def write_toml(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        "\n".join(
            [
                f'host = "{data["host"]}"',
                f"port = {data['port']}",
                "",
                "[credentials]",
                f'username = "{data["credentials"]["username"]}"',
                f'password = "{data["credentials"]["password"]}"',
            ]
        ),
        encoding="utf-8",
    )


def write_ini(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        "\n".join(
            [
                "[DEFAULT]",
                f"host = {data['host']}",
                f"port = {data['port']}",
                "",
                "[credentials]",
                f"username = {data['credentials']['username']}",
                f"password = {data['credentials']['password']}",
            ]
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "loader_type,suffix,writer",
    [
        (ObjectLoaderJson, ".json", write_json),
        (ObjectLoaderYaml, ".yaml", write_yaml),
        (ObjectLoaderToml, ".toml", write_toml),
        (ObjectLoaderIni, ".ini", write_ini),
    ],
)
def test_object_file_loaders_load_model(
    tmp_path: Path,
    loader_type,
    suffix: str,
    writer: Callable[[Path, dict[str, object]], None],
):
    data = {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "admin",
            "password": "secret",
        },
    }
    path = tmp_path / f"config{suffix}"
    writer(path, data)

    result = loader_type[ServiceConfig](path=path).load()

    assert result == ServiceConfig(
        host="localhost",
        port=5432,
        credentials=Credentials(
            username="admin",
            password="secret",
        ),
    )


@pytest.mark.parametrize(
    "loader_type,suffix,content",
    [
        (ObjectLoaderJson, ".json", '{"foo": "configured"}'),
        (ObjectLoaderYaml, ".yaml", "foo: configured\n"),
        (ObjectLoaderToml, ".toml", 'foo = "configured"\n'),
        (ObjectLoaderIni, ".ini", "[DEFAULT]\nfoo = configured\n"),
    ],
)
def test_object_file_loaders_apply_discriminator_default(tmp_path: Path, loader_type, suffix: str, content: str):
    path = tmp_path / f"store{suffix}"
    path.write_text(content, encoding="utf-8")

    result = loader_type[RoleStore](
        path=path,
        default_discriminator_value="A",
    ).load()

    assert result == DummyStoreA(foo="configured")


def test_object_file_loader_raises_for_missing_file(tmp_path: Path):
    loader = ObjectLoaderJson[ServiceConfig](path=tmp_path / "missing.json")

    with pytest.raises(RuntimeError, match="Configuration file does not exist"):
        loader.load()


def test_object_file_loader_raises_for_non_object_file(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    loader = ObjectLoaderJson[ServiceConfig](path=path)

    with pytest.raises(RuntimeError, match="to contain an object, found list"):
        loader.load()
