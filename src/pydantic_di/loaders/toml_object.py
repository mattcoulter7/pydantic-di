"""TOML-backed object loader implementation."""

import tomllib
from typing import Any, Literal, override

from pydantic_di.schema.loader_type import LoaderSource

from .file_object import ObjectLoaderFileBase


class ObjectLoaderToml[T](ObjectLoaderFileBase[T]):
    """Load a structured object from a local TOML file."""

    source: Literal[LoaderSource.TOML_OBJECT] = LoaderSource.TOML_OBJECT

    @override
    def parse_file(self) -> dict[str, Any]:
        """Read and parse the configured TOML file."""
        with self.path.open("rb") as file:
            return tomllib.load(file)
