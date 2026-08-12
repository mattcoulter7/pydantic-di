"""Environment-backed object loader implementation."""

import os
from typing import Any, Literal, override

from pydantic import model_validator

from pydantic_di.schema.loader_type import LoaderSource
from pydantic_di.utils import extract_env_tree, to_env_prefix

from .base import ObjectLoaderBase, T


class ObjectLoaderEnvironment(ObjectLoaderBase[T]):
    """Load structured objects from environment variables.

    Data is collected using a configurable prefix and reshaped to match
    the target model schema.
    """

    # These get pulled from env or you can override in code:
    source: Literal[LoaderSource.ENVIRONMENT_OBJECT] = LoaderSource.ENVIRONMENT_OBJECT

    env_prefix: str | None = None

    @model_validator(mode="after")
    def default_env_prefix(self):
        """Populate a default prefix from the inferred alias name."""
        if self.env_prefix is None:
            self.env_prefix = to_env_prefix(self.alias_name)
        return self

    @override
    def load_raw(
        self,
    ) -> dict[str, Any]:
        """Build a nested dictionary from environment keys for model parsing."""
        tree = extract_env_tree(
            os.environ,
            self.env_prefix,
        )

        return self.prepare_object_data(tree)
