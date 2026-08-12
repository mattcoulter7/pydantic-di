"""YAML-backed object loader implementation."""

from typing import Any, Literal, override

import yaml

from pydantic_di.schema.loader_type import LoaderSource

from .base import T
from .file_object import ObjectLoaderFileBase


class ObjectLoaderYaml(ObjectLoaderFileBase[T]):
    """Load a structured object from a local YAML file."""

    source: Literal[LoaderSource.YAML_OBJECT] = LoaderSource.YAML_OBJECT

    @override
    def parse_file(self) -> dict[str, Any]:
        """Read and parse the configured YAML file."""
        with self.path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)
