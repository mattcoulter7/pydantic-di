"""INI-backed object loader implementation."""

from configparser import ConfigParser
from typing import Any, Literal, override

from pydantic_di.schema.loader_type import LoaderSource

from .base import T
from .file_object import ObjectLoaderFileBase


class ObjectLoaderIni(ObjectLoaderFileBase[T]):
    """Load a structured object from a local INI file."""

    source: Literal[LoaderSource.INI_OBJECT] = LoaderSource.INI_OBJECT

    @override
    def parse_file(self) -> dict[str, Any]:
        """Read and parse the configured INI file."""
        parser = ConfigParser()
        parser.read(self.path, encoding="utf-8")

        data: dict[str, Any] = dict(parser.defaults())

        for section in parser.sections():
            data[section] = dict(parser[section])

        return data
