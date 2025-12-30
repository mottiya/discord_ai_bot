import asyncio
import logging

import discord

from src.message_generator import BaseMessageGenerator

logger = logging.getLogger(__name__)


class DiscordClient(discord.Client):
    def __init__(
        self,
        id: int,
        token: str,
        channel_id: int,
        oponent_id: int,
        message_generator: BaseMessageGenerator,
        **options,
    ):
        self.token = token
        self.channel_id = channel_id
        self.oponent_id = oponent_id
        self.stop_event = asyncio.Event()
        self.message_generator = message_generator
        self.message_count = 0  # Счетчик сообщений в текущей сессии
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

    async def start_conversation(self) -> None:
        """
        Начинает диалог, отправляя первое сообщение.
        Вызывается для первого бота после готовности обоих ботов.
        """
        channel = self.get_channel(self.channel_id)
        if channel is None:
            logger.error(f"Channel {self.channel_id} not found")
            return

        # Генерируем первое сообщение (без сообщения оппонента)
        first_message = await self.message_generator.get_next_message(
            current_identity_id=self.user.id,
            opponent_message=None,
            message_count=self.message_count,
        )
        if first_message is None:
            logger.warning("Не удалось сгенерировать первое сообщение")
            return

        await self.send_msg(first_message)
        self.message_count += 1
        logger.info(f"Начало диалога: отправлено первое сообщение от {self.user.id}")

    async def on_message(self, message: discord.Message) -> None:
        if (
            message.channel.id != self.channel_id
            or message.author.id == self.user.id
            or message.reference is None
        ):
            return

        if message.author.id == self.oponent_id:
            # Получаем текст сообщения оппонента
            opponent_message_text = message.content if message.content else None

            # Генерируем ответ с учетом контекста
            next_message = await self.message_generator.get_next_message(
                current_identity_id=self.user.id,
                opponent_message=opponent_message_text,
                message_count=self.message_count,
            )
            if next_message is None:
                self.stop_event.set()
                return
            await self.send_msg(next_message, message)
            self.message_count += 1
            return

        referenced_message = message.reference.resolved
        if (
            referenced_message is None
            or referenced_message.author.id != self.user.id
        ):
            return

        await self.send_msg(f"Hello to {message.author.id} from {self.user.id}!", message)
