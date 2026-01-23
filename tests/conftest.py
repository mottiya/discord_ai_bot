import pytest

from src.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=".env.test")
