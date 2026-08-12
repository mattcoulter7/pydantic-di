"""Singleton registry used for persisted dependency instances."""

from typing import Any

from pydantic import BaseModel

from .types import LoadTarget


class SingletonRegistryMeta(type):
    """Metaclass that memoizes constructed instances by key."""

    _instances: dict[tuple[Any, Any], BaseModel] = {}

    def __call__[T: BaseModel](cls, loader: LoadTarget[T], key: Any) -> T:
        """Return a cached instance for `key`, creating it if needed."""
        if key not in cls._instances:
            cls._instances[key] = loader()
        return cls._instances[key]  # type: ignore


class SingletonRegistry(metaclass=SingletonRegistryMeta):
    """Singleton entry point backed by `SingletonRegistryMeta`."""
