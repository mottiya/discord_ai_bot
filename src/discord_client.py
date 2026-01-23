import asyncio
import logging

import discord

from src.ai.graph import DiscordChatMessage, IdentityState
from src.ai.graph import app as llm_app

logger = logging.getLogger(__name__)


class ChannelNotFound(Exception):
    pass


class DiscordClient(discord.Client):
    def __init__(
        self,
        token: str,
        channel_id: int,
        opponent_id: int,
        state: IdentityState,
        **options,
    ):
        self.token = token
        self.channel_id = channel_id
        self.opponent_id = opponent_id

        self.state = state
        self.llm_app = llm_app
        self.ready_event = asyncio.Event()

        super().__init__(**options)

    def start(self) -> asyncio.Task:
        return asyncio.create_task(super().start(self.token))

    async def send_msg(
        self,
        message: str,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage | None = None,
    ) -> discord.Message:
        channel = self.get_channel(self.channel_id)
        if channel is None:
            raise ChannelNotFound()
        async with channel.typing():
            await asyncio.sleep(5)
        return await channel.send(message, reference=reference)

    async def on_ready(self) -> None:
        self.ready_event.set()
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel_id or message.author.id == self.user.id:
            return

        referenced_message = None
        if message.reference is not None:
            referenced_message = message.reference.resolved

        if message.author.id == self.opponent_id or (
            referenced_message is not None and referenced_message.author.id == self.user.id
        ):
            self.state.messages.append(
                DiscordChatMessage(
                    content=message.content,
                    author_id=message.author.id,
                    author_name=message.author.name,
                    reply_id=None if referenced_message is None else referenced_message.author.id,
                    reply_name=None if referenced_message is None else referenced_message.author.name,
                )
            )
            self.state.clear()
            try:
                response: dict = await llm_app.ainvoke(self.state)
                if response.get("response_msg") is None:
                    logger.error("LLM вернул пустой ответ")
                    return
                await self.send_msg(response["response_msg"].content, message)
            except Exception:
                logger.exception("Ошибка при обработке сообщения")
            return
