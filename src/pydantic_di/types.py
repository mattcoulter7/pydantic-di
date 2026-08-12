"""Common typing aliases for dependency loading."""

from collections.abc import Callable
from typing import (
    Annotated,
    Any,
)

from .loaders.base import LoaderBase

type LoadTarget[T] = Callable[..., T] | type[T] | LoaderBase[T] | Annotated[T | Any, Any]
