import pytest

from src.discord_client import DiscordClient
from src.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=".env.test"
    )

@pytest.fixture
def discord_client(settings: Settings) -> DiscordClient:
    return DiscordClient(settings=settings)
