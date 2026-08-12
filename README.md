# pydantic-di

A lightweight dependency loading and injection package for Python.

`pydantic-di` provides a small dependency system for loading objects from environment variables, Python callables, Pydantic models, attrs classes, and custom loaders. It is designed to feel familiar if you have used FastAPI dependencies, while also working outside FastAPI.

## Migration from auth-broker

As of `pydantic-di` version `0.2.2`, this package has moved out of the
`auth-broker` organisation, been renamed, and had its import namespace updated.

| Item | Previous | Current |
| --- | --- | --- |
| GitHub repository | [`auth-broker/package-dependency`](https://github.com/auth-broker/package-dependency) | [`mattcoulter7/pydantic-di`](https://github.com/mattcoulter7/pydantic-di) |
| PyPI package | [`ab-dependency`](https://pypi.org/project/ab-dependency/) | [`pydantic-di`](https://pypi.org/project/pydantic-di/) |
| Install command | `pip install ab-dependency` | `pip install pydantic-di` |
| Import namespace | `ab_core.dependency` | `pydantic_di` |

The old PyPI package is retained as an archived historical package. New work
should use `pydantic-di` and `pydantic_di`.

## Features

- Load Pydantic models from environment variables
- Load primitive values from environment variables
- Support discriminated unions
- Support attrs classes by converting them to Pydantic-compatible models
- Support singleton-style persistent dependencies
- Support transient dependencies
- Inject dependencies into:
  - sync functions
  - async functions
  - sync generators
  - async generators
  - classes
  - Pydantic models
- Support generator dependency cleanup
- Support FastAPI dependency integration
- Support flattened environment variable conventions
- Support JSON serialised complex values, such as lists

## Installation

```bash
pip install pydantic-di
```

Or with `uv`:

```bash
uv add pydantic-di
```

## Basic usage

```python
from pydantic import BaseModel

from pydantic_di import Load


class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080


config = Load(AppConfig)

print(config.host)
print(config.port)
```

By default, object models are loaded from environment variables using the model name converted to env-var style.

For `AppConfig`, the default prefix is:

```text
APP_CONFIG
```

So these environment variables:

```bash
APP_CONFIG_HOST=0.0.0.0
APP_CONFIG_PORT=8000
```

produce:

```python
AppConfig(host="0.0.0.0", port=8000)
```

## Environment variable naming

Model names are converted from PascalCase or camelCase to uppercase snake case.

```python
OAuth2TokenStore -> O_AUTH2_TOKEN_STORE
HTTPServerConfig -> HTTP_SERVER_CONFIG
AppConfig        -> APP_CONFIG
```

Field names are appended to the prefix.

```bash
APP_CONFIG_HOST=0.0.0.0
APP_CONFIG_PORT=8000
```

Nested field names are flattened using underscores.

```python
class DatabaseConfig(BaseModel):
    host: str
    port: int


class AppConfig(BaseModel):
    database: DatabaseConfig
```

```bash
APP_CONFIG_DATABASE_HOST=localhost
APP_CONFIG_DATABASE_PORT=5432
```

## Loading primitive values

Use `LoaderEnvironment` when loading a single primitive value from a specific environment variable.

```python
from pydantic_di.loaders import LoaderEnvironment

port = LoaderEnvironment[int](key="PORT").load()
```

```bash
PORT=8080
```

The value is validated and cast using Pydantic.

## Loader defaults

There are two default mechanisms with different semantics:

- `default_value`: whole-result fallback when no source value is loaded.
- `default_values`: object-field defaults for model loaders, merged with loaded values.

### Whole-result fallback (`default_value`)

Use this for scalar or single-value loaders.

```python
from pydantic_di.loaders import LoaderEnvironment

port = LoaderEnvironment[int](
    key="PORT",
    default_value=8080,
).load()
```

If `PORT` is missing, this returns `8080`.

Falsy defaults are supported, including `0`, `False`, and empty strings.

### Partial object defaults (`default_values`)

Use this with object loaders to provide field-level defaults that are merged with loaded values.

```python
from pydantic import BaseModel
from pydantic_di.loaders import ObjectLoaderEnvironment


class Credentials(BaseModel):
    username: str
    password: str


class ServiceConfig(BaseModel):
    api_key: str
    port: int
    credentials: Credentials


config = ObjectLoaderEnvironment[ServiceConfig](
    env_prefix="MY_CONFIG",
    default_values={
        "api_key": "default",
        "port": 5432,
        "credentials": {
            "username": "admin",
            "password": "secret",
        },
    },
).load()
```

With:

```bash
MY_CONFIG_PORT=6432
MY_CONFIG_CREDENTIALS_USERNAME=matt
```

The effective data is:

```python
{
    "api_key": "default",  # from default_values
    "port": "6432",  # from env
    "credentials": {
        "username": "matt",  # from env
        "password": "secret",  # from default_values
    },
}
```

Important notes:

- `default_values` should be provided in model-field shape.
- Environment values always override defaults for matching leaves.
- Environment key flattening and field alignment are applied to loaded source data.

## Persistent dependencies

`Load(..., persist=True)` caches the loaded dependency.

```python
from pydantic import BaseModel
from pydantic_di import Load


class Client(BaseModel):
    name: str = "client"


one = Load(Client, persist=True)
two = Load(Client, persist=True)

assert one is two
```

Transient dependencies are created each time.

```python
one = Load(Client, persist=False)
two = Load(Client, persist=False)

assert one is not two
assert one == two
```

## Lazy dependencies

Use `Depends` to defer loading until call time.

```python
from typing import Annotated

from pydantic import BaseModel

from pydantic_di import Depends, inject


class Settings(BaseModel):
    value: str = "hello"


@inject
def run(settings: Annotated[Settings, Depends(Settings)]):
    return settings.value


assert run() == "hello"
```

## Function injection

```python
from typing import Annotated

from pydantic import BaseModel

from pydantic_di import Depends, inject


class Database(BaseModel):
    url: str = "sqlite://"


@inject
def handler(db: Annotated[Database, Depends(Database)]):
    return db.url
```

Dependencies are only resolved when the argument was not explicitly provided.

```python
handler(Database(url="postgresql://"))
```

## Async function injection

```python
from typing import Annotated

from pydantic_di import Depends, inject


async def make_token() -> str:
    return "abc"


@inject
async def handler(token: Annotated[str, Depends(make_token)]):
    return token
```

## Generator dependency support

Generator dependencies are entered before the function runs and cleaned up afterwards.

```python
from typing import Annotated

from pydantic_di import Depends, inject


def resource():
    try:
        yield "resource"
    finally:
        print("closed")


@inject
def handler(value: Annotated[str, Depends(resource)]):
    return value
```

Exceptions are thrown back into the generator so `except` and `finally` blocks can run.

```python
def resource():
    try:
        yield "resource"
    except Exception:
        print("caught")
        raise
    finally:
        print("closed")
```

## Class injection

```python
from typing import Annotated

from pydantic import BaseModel

from pydantic_di import Depends, inject


class Settings(BaseModel):
    value: str = "hello"


@inject
class Service:
    settings: Annotated[Settings, Depends(Settings)]

    def run(self):
        return self.settings.value
```

## Pydantic model injection

```python
from typing import Annotated

from pydantic import BaseModel

from pydantic_di import Depends, inject


class Settings(BaseModel):
    value: str = "hello"


@inject
class AppConfig(BaseModel):
    settings: Annotated[Settings, Depends(Settings)]
    retries: int = 3
```

If a field is supplied by input data, the dependency is not resolved.

## FastAPI integration

`Depends` subclasses FastAPI's dependency parameter when FastAPI is installed.

```python
from typing import Annotated

from fastapi import Depends as FDepends, FastAPI
from pydantic import BaseModel

from pydantic_di import Depends, inject


class SomeDependency(BaseModel):
    value: str = "injected"


def provide_dependency() -> SomeDependency:
    return SomeDependency()


@inject
def context(dep: Annotated[SomeDependency, Depends(provide_dependency)]):
    try:
        yield dep
    finally:
        pass


app = FastAPI()


@app.get("/")
def route(dep: Annotated[SomeDependency, FDepends(context)]):
    return {"value": dep.value}
```

## Discriminated unions

Discriminated unions are supported through Pydantic's `Discriminator`.

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator

from pydantic_di import Load


class FileStore(BaseModel):
    type: Literal["FILE"] = "FILE"
    path: str


class S3Store(BaseModel):
    type: Literal["S3"] = "S3"
    bucket: str


Store = Annotated[FileStore | S3Store, Discriminator("type")]

store = Load(Store)
```

Environment variables:

```bash
STORE_TYPE=S3
STORE_S3_BUCKET=my-bucket
```

Result:

```python
S3Store(type="S3", bucket="my-bucket")
```

## Flattened discriminator convention

For discriminated unions, the discriminator selects which nested branch is used.

```bash
DUMMY_STORE_TYPE=A
DUMMY_STORE_A_FOO=hello
DUMMY_STORE_A_NUM=42
```

This becomes:

```python
{
    "type": "A",
    "foo": "hello",
    "num": 42,
}
```

## attrs support

attrs classes can be loaded by converting them into Pydantic-compatible models.

```python
import attrs

from pydantic_di import Load
from pydantic_di.pydanticize import pydanticize_type


@attrs.define
class Settings:
    host: str = "localhost"
    port: int = 8080


SettingsModel = pydanticize_type(Settings)
settings = Load(SettingsModel)
```

attrs defaults and factories are preserved.

## List support

Simple lists can be supplied as JSON strings.

```python
from pydantic import BaseModel

from pydantic_di import Load


class Config(BaseModel):
    values: list[str]
```

```bash
CONFIG_VALUES='["A", "B", "C"]'
```

Result:

```python
Config(values=["A", "B", "C"])
```

## Planned recursive list environment convention

For recursive object loading, lists may also be represented as indexed environment variables.

Simple values:

```bash
CONFIG_VALUES_0=A
CONFIG_VALUES_1=B
CONFIG_VALUES_2=C
```

Equivalent JSON form:

```bash
CONFIG_VALUES='["A", "B", "C"]'
```

Lists of Pydantic models:

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator


class BlahItem(BaseModel):
    type: Literal["blah"] = "blah"
    label: str


class OtherItem(BaseModel):
    type: Literal["other"] = "other"
    label: str


Item = Annotated[BlahItem | OtherItem, Discriminator("type")]


class SomeObject(BaseModel):
    list_field: list[Item]
```

Environment variables:

```bash
SOME_OBJECT_LIST_FIELD_0_TYPE=blah
SOME_OBJECT_LIST_FIELD_0_BLAH_LABEL=first
SOME_OBJECT_LIST_FIELD_1_TYPE=other
SOME_OBJECT_LIST_FIELD_1_OTHER_LABEL=second
```

Expected result:

```python
SomeObject(
    list_field=[
        BlahItem(type="blah", label="first"),
        OtherItem(type="other", label="second"),
    ]
)
```

This keeps backwards compatibility with the existing JSON form while allowing recursive, schema-aware environment unpacking.

## Custom loaders

Create a custom loader by subclassing `LoaderBase`.

```python
from typing import Any

from pydantic_di.loaders.base import LoaderBase


class MyLoader(LoaderBase[str]):
    key: str

    def load_raw(self) -> Any:
        return f"value-for-{self.key}"
```

Then use it directly:

```python
loader = MyLoader[str](key="example")
value = loader.load()
```

## Public API

```python
from pydantic_di import (
    Depends,
    Load,
    inject,
    sentinel,
    pydanticize_data,
    pydanticize_type,
    pydanticize_object,
    cached_type_adapter,
    is_supported_by_pydantic,
)
```

## Design notes

`Load` resolves immediately.

```python
settings = Load(Settings)
```

`Depends` resolves lazily.

```python
settings: Annotated[Settings, Depends(Settings)]
```

`persist=True` caches by load target or loaded type.

```python
Depends(Settings, persist=True)
```

`persist=False` creates a fresh dependency each time.

```python
Depends(Settings, persist=False)
```

## Development

Run tests:

```bash
pytest
```

Run formatting and linting:

```bash
ruff check .
ruff format .
```

## Compatibility goals

The package aims to keep existing behaviour stable:

* Existing JSON list loading should continue to work.
* Existing flat object env-var loading should continue to work.
* Existing discriminator conventions should continue to work.
* New recursive list loading should be additive.
