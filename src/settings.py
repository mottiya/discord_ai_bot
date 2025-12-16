from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AISettings(BaseModel):
    model: str = ""


class Settings(BaseSettings):
    ai: AISettings = Field(default_factory=AISettings)
