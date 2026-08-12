"""JSON-backed object loader implementation."""

import json
from typing import Any, Literal, override

from pydantic_di.schema.loader_type import LoaderSource

from .file_object import ObjectLoaderFileBase


class ObjectLoaderJson[T](ObjectLoaderFileBase[T]):
    """Load a structured object from a local JSON file."""

    source: Literal[LoaderSource.JSON_OBJECT] = LoaderSource.JSON_OBJECT

    @override
    def parse_file(self) -> dict[str, Any]:
        """Read and parse the configured JSON file."""
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)
