from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="settings/.env", env_file_encoding="utf-8", extra="ignore"
    )


class DatabaseConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="db_")

    host: str
    password: SecretStr