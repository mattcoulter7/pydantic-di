"""Loader type exports and tagged union helpers."""

from typing import Annotated

from pydantic import Discriminator

from .environment import LoaderEnvironment
from .environment_object import ObjectLoaderEnvironment
from .ini_object import ObjectLoaderIni
from .json_object import ObjectLoaderJson
from .template import LoaderTemplate
from .toml_object import ObjectLoaderToml
from .yaml_object import ObjectLoaderYaml

Loader = Annotated[
    ObjectLoaderEnvironment
    | ObjectLoaderJson
    | ObjectLoaderYaml
    | ObjectLoaderToml
    | ObjectLoaderIni
    | LoaderEnvironment
    | LoaderTemplate,
    Discriminator("source"),
]
