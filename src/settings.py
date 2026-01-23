from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_NESTED_DELIMITER = "__"
ENV_PREFIX = f"DBA{ENV_NESTED_DELIMITER}"


class LogSettings(BaseModel):
    level: Literal[10, 20, 30, 40, 50] = 20
    format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    filename: str = "app.log"


class AISettings(BaseModel):
    model: str
    api_key: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)


class IdentitySettings(BaseModel):
    id: int
    token: str


class DiscordSettings(BaseModel):
    channel_id: int
    identity_1: IdentitySettings
    identity_2: IdentitySettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=ENV_PREFIX,
        env_nested_delimiter=ENV_NESTED_DELIMITER,
    )

    discord: DiscordSettings
    main_ai: AISettings = Field(default_factory=AISettings)
    log: LogSettings = Field(default_factory=LogSettings)
    resource_path: Path = Path("./resources")
    model_promts_file: Path = resource_path.joinpath("model_promts.yaml")
    session_timeout: int = Field(default=1200, ge=60, description="Таймаут сессии в секундах")

    @computed_field
    @property
    def log_file(self) -> Path:
        return self.resource_path.joinpath(self.log.filename)
