import pytest

from src.settings import Settings


@pytest.mark.asyncio
async def test_settings(settings: Settings):
    assert settings.discord.channel_id is not None
