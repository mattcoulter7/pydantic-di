"""File-backed object loader base implementation."""

from abc import abstractmethod
from pathlib import Path
from typing import Any, override

from .base import ObjectLoaderBase, T


class ObjectLoaderFileBase(ObjectLoaderBase[T]):
    """Base loader for structured configuration stored in a local file."""

    path: Path

    @abstractmethod
    def parse_file(self) -> dict[str, Any]:
        """Read and parse the configured file into a dictionary."""
        ...

    @override
    def load_raw(
        self,
    ) -> dict[str, Any]:
        """Read and prepare object data from a configured local file."""
        if not self.path.exists():
            raise FileNotFoundError(f"Configuration file does not exist: {self.path}")

        if not self.path.is_file():
            raise ValueError(f"Configuration path is not a file: {self.path}")

        data = self.parse_file()

        if not isinstance(data, dict):
            raise TypeError(
                f"Expected configuration file `{self.path}` to contain an object, found {type(data).__name__}."
            )

        return self.prepare_object_data(data)
