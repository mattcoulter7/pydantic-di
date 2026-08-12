"""Typed sentinel helper for dependency-injection defaults."""

from typing import cast

_INJECT_SENTINEL = object()  # unique, never used at runtime


def sentinel[T]() -> T:  # noqa: N802  (capital I for clarity)
    """Typing-only sentinel for DI parameters.

    Usage:
        db: Annotated[Database, Depends(make_db)] = Sentinel()
    """
    return cast(T, _INJECT_SENTINEL)
