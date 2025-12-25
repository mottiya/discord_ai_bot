from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_NESTED_DELIMITER = "__"
ENV_PREFIX = f"DBA{ENV_NESTED_DELIMITER}"

class AISettings(BaseModel):
    model: str = ""


class IdentitySettings(BaseModel):
    id: int
    token: str

class BaseDiscordSettings(BaseModel):
    channel_id: int

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix=ENV_PREFIX,
        env_nested_delimiter=ENV_NESTED_DELIMITER,
    )

    discord: BaseDiscordSettings
    identity_1: IdentitySettings
    identity_2: IdentitySettings
    ai: AISettings = Field(default_factory=AISettings)
    launch_type: Literal["CRON"] = "CRON"
    resource_path: Path = Path("./resources")
    scenarios_file: Path = resource_path.joinpath("scenarios.json")

    log_level: Literal[10, 20, 30, 40, 50] = 20
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    log_file: Path = resource_path.joinpath("app.log")
