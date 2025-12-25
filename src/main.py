import asyncio

from src.discord_client import DiscordClient
from src.logger import setup_logging
from src.message_generator import MessageGenerator
from src.resources_manager import load_scenarios
from src.settings import Settings


async def main():
    settings = Settings()
    setup_logging(settings)
    scenarios = await load_scenarios(settings.scenarios_file)
    message_generator = MessageGenerator(scenarios)
    client1 = DiscordClient(
        settings.identity_1.id,
        settings.identity_1.token,
        settings.discord.channel_id,
        settings.identity_2.id,
        message_generator,
    )
    client2 = DiscordClient(
        settings.identity_2.id,
        settings.identity_2.token,
        settings.discord.channel_id,
        settings.identity_1.id,
        message_generator,
    )
    task1 = client1.start_bot()
    task2 = client2.start_bot()
    await asyncio.wait(
        [asyncio.create_task(client1.stop_event.wait()), asyncio.create_task(client2.stop_event.wait())],
        return_when=asyncio.FIRST_COMPLETED,
    )
    task1.cancel()
    task2.cancel()
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())
