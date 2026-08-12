"""Loader source discriminator values."""

from enum import StrEnum


class LoaderSource(StrEnum):
    """Supported loader source identifiers."""

    ENVIRONMENT = "ENVIRONMENT"
    ENVIRONMENT_OBJECT = "ENVIRONMENT_OBJECT"
    JSON_OBJECT = "JSON_OBJECT"
    YAML_OBJECT = "YAML_OBJECT"
    TOML_OBJECT = "TOML_OBJECT"
    INI_OBJECT = "INI_OBJECT"
    TEMPLATE = "TEMPLATE"
