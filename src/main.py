import asyncio
import logging

from src.ai.graph import DiscordChatMessage, create_identity_state
from src.ai.llm_getter import setup_model
from src.discord_client import DiscordClient
from src.logger import setup_logging
from src.resources_manager import ModelPromts, load_model
from src.settings import IdentitySettings, Settings

logger = logging.getLogger(__name__)


class IdentityNotFoundError(Exception):
    def __init__(self, identity_id: int):
        super().__init__(f"Identity с ID {identity_id} не найдена в конфигурации промптов")
        self.identity_id = identity_id


def validate_identities(settings: Settings, prompts: ModelPromts) -> None:
    for identity in [settings.discord.identity_1, settings.discord.identity_2]:
        if identity.id not in prompts.identities:
            raise IdentityNotFoundError(identity.id)


def build_identity_state(
    identity_settings: IdentitySettings,
    prompts: ModelPromts,
    messages: list[DiscordChatMessage],
    llm,
):
    identity = prompts.identities[identity_settings.id]
    return create_identity_state(
        messages=messages,
        discord_id=identity_settings.id,
        system_message=identity.system_message,
        system_prompt=identity.system_prompt,
        name=identity.name,
        llm=llm,
    )


async def main():
    settings = Settings()
    setup_logging(settings)

    system_promts = await load_model(ModelPromts, settings.model_promts_file)
    validate_identities(settings, system_promts)

    llm = await setup_model(settings)

    messages = []

    init_state1 = build_identity_state(settings.discord.identity_1, system_promts, messages, llm)
    init_state2 = build_identity_state(settings.discord.identity_2, system_promts, messages, llm)

    init_message = system_promts.identities[settings.discord.identity_1.id].init_message
    messages.append(
        DiscordChatMessage(
            content=init_message,
            author_id=init_state1.discord_id,
            author_name=init_state1.discord_name,
        )
    )

    client1 = DiscordClient(
        settings.discord.identity_1.token,
        settings.discord.channel_id,
        settings.discord.identity_2.id,
        init_state1,
    )
    client2 = DiscordClient(
        settings.discord.identity_2.token,
        settings.discord.channel_id,
        settings.discord.identity_1.id,
        init_state2,
    )

    try:
        client1.start()
        client2.start()

        await asyncio.gather(
            client1.ready_event.wait(),
            client2.ready_event.wait(),
        )

        await client1.send_msg(init_message)

        await asyncio.sleep(settings.session_timeout)

        await asyncio.gather(
            client1.close(),
            client2.close(),
        )
    except Exception as e:
        logger.error(f"Критическая ошибка в работе приложения: {e}", exc_info=True)
        return


if __name__ == "__main__":
    asyncio.run(main())
