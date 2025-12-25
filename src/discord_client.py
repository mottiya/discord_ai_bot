import asyncio
import logging

import discord

from src.message_generator import MessageGenerator

logger = logging.getLogger(__name__)


class DiscordClient(discord.Client):
    def __init__(
        self,
        id: int,
        token: str,
        channel_id: int,
        oponent_id: int,
        message_generator: MessageGenerator,
        **options,
    ):
        self.token = token
        self.channel_id = channel_id
        self.oponent_id = oponent_id
        self.stop_event = asyncio.Event()
        self.message_generator = message_generator
        super().__init__(**options)

    def start_bot(self) -> asyncio.Task:
        return asyncio.create_task(self.start(self.token))

    async def send_msg(
        self,
        message: str,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage | None = None,
    ) -> discord.Message:
        channel = self.get_channel(self.channel_id)
        async with channel.typing():
            await asyncio.sleep(5)
        return await channel.send(message, reference=reference)

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

    async def on_message(self, message: discord.Message) -> None:
        if (
            message.channel.id != self.channel_id
            or message.author.id == self.user.id
            or message.reference is None
        ):
            return

        if message.author.id == self.oponent_id:
            next_message = await self.message_generator.get_next_message()
            if next_message is None:
                self.stop_event.set()
                return
            await self.send_msg(next_message, message)
            return

        referenced_message = message.reference.resolved
        if (
            referenced_message is None
            or referenced_message.author.id != self.user.id
        ):
            return

        await self.send_msg(f"Hello to {message.author.id} from {self.user.id}!", message)
