import asyncio
import logging
import sys

from src.ai_agent import get_model
from src.ai_message_generator import AIMessageGenerator
from src.discord_client import DiscordClient
from src.logger import setup_logging
from src.message_generator import BaseMessageGenerator, JsonScenarioMessageGenerator
from src.resources_manager import load_scenarios, load_system_context
from src.settings import Settings

logger = logging.getLogger(__name__)


async def main():
    settings = Settings()
    setup_logging(settings)

    # Выбираем генератор в зависимости от режима
    if settings.generation_mode == "AI":
        logger.info("Используется режим генерации: AI")
        # Загружаем системный контекст
        system_context = await load_system_context(settings.system_context_file)
        # Создаем модель
        model = await get_model(settings)
        # Создаем AI генератор
        message_generator: BaseMessageGenerator = AIMessageGenerator(
            model=model,
            system_context=system_context,
            settings=settings,
            identity_1_id=settings.identity_1.id,
            identity_2_id=settings.identity_2.id,
        )
    else:
        logger.info("Используется режим генерации: JSON")
        # Загружаем сценарии
        scenarios = await load_scenarios(settings.scenarios_file)
        # Создаем JSON генератор
        message_generator = JsonScenarioMessageGenerator(scenarios)

    # Создаем клиенты Discord
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

    try:
        task1 = client1.start_bot()
        task2 = client2.start_bot()

        # Ждем готовности обоих ботов
        ready_event_1 = asyncio.Event()
        ready_event_2 = asyncio.Event()

        original_on_ready_1 = client1.on_ready
        original_on_ready_2 = client2.on_ready

        async def on_ready_wrapper_1():
            await original_on_ready_1()
            ready_event_1.set()

        async def on_ready_wrapper_2():
            await original_on_ready_2()
            ready_event_2.set()

        client1.on_ready = on_ready_wrapper_1
        client2.on_ready = on_ready_wrapper_2

        # Ждем готовности обоих ботов
        await asyncio.gather(ready_event_1.wait(), ready_event_2.wait())

        # Первый бот начинает диалог
        await client1.start_conversation()

        # Ждем завершения работы
        await asyncio.wait(
            [asyncio.create_task(client1.stop_event.wait()), asyncio.create_task(client2.stop_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )
        task1.cancel()
        task2.cancel()
        await asyncio.gather(task1, task2, return_exceptions=True)
    except Exception as e:
        logger.error(f"Критическая ошибка в работе приложения: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
