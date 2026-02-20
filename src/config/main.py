from typing import Self

from .env_config import DatabaseConfig

from pydantic import Field
from pydantic_settings import BaseSettings, TomlConfigSettingsSource

from .toml_config import FastapiConfig


class Config(BaseSettings):
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    fastapi: FastapiConfig

    @classmethod
    def load(cls) -> Self:
        return cls()

    @classmethod
    def settings_customise_sources(cls, settings_cls, **kwargs):
        return (TomlConfigSettingsSource(settings_cls, "settings/config.toml"),)