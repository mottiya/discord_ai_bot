import asyncio
import random
import time
from datetime import datetime, timedelta

# === ИМПОРТЫ ДЛЯ AI, ДОКУМЕНТАЦИИ И ЛИЧНОСТИ — СТРОКИ 6–8 ===
from ai.provider import generate_response
from knowledge.loader import load_docs_for_server
from agents.personality import get_personality

class AIAgent:
    # === КОНСТРУКТОР — СТРОКИ 12–18 (исправьте init → __init__) ===
    def init(self, client, partner_id, server_configs, personality):
        self.client = client
        self.partner_id = partner_id
        self.server_configs = server_configs
        self.personality = personality
        self.ignore_list = {}
        self.current_sessions = {}

    # === ГЕНЕРАЦИЯ ОТВЕТА ЧЕРЕЗ GEMINI — СТРОКИ 21–46 ===
    async def _generate_ai_response(self, message):
        server_id = str(message.guild.id)
        config = self.server_configs[server_id]
        
        # Загрузка документации
        docs = load_docs_for_server(server_id, self.server_configs)
        context = docs["text"][:5000]  # Ограничение длины

        # Получение описания личности
        personality_desc = get_personality(self.personality)

        # Чёткий промпт для Gemini
        full_prompt = (
            f"Контекст проекта:\n{context}\n\n"
            f"Твоя роль: {personality_desc}\n\n"
            f"На основе этого, дай осмысленный и дружелюбный ответ на сообщение: {message.content}"
        )

        try:
            response = await generate_response(
                provider="google",
                model="gemini-1.5-pro",
                messages=[{"role": "user", "content": full_prompt}],
                context=context
            )
            return response.strip()
        except Exception as e:
            return f"[AI error] Но я всё равно здесь!"

    # === ОТВЕТ ПАРТНЁРУ — СТРОКИ 49–51 ===
    async def respond_to_partner(self, message):
        response = await self._generate_ai_response(message)
        await self.send_with_delay(message.channel, response)

    # === ОТВЕТ СТОРОННЕМУ — СТРОКИ 54–60 ===
    async def handle_stranger(self, message):
        response = await self._generate_ai_response(message)
        await self.send_with_delay(message.channel, response)
        # Добавить в игнор на 4 часа
        server_id = str(message.guild.id)
        config = self.server_configs[server_id]
        ignore_hours = config.get("ignore_reset_hours", 4)
        self.ignore_list[message.author.id] = time.time() + ignore_hours * 3600

    # === ОСТАЛЬНОЙ КОД (он у вас уже есть, но оставим для полноты) ===
    async def on_message(self, message):
        if message.author.id == self.client.user.id:
            return
        if message.guild is None:
            return

        server_id = str(message.guild.id)
        if server_id not in self.server_configs:
            return

        config = self.server_configs[server_id]
        channel_id = config.get("channel_id")
        if channel_id and message.channel.id != channel_id:
            return

        if message.author.id in self.ignore_list:
            if time.time() < self.ignore_list[message.author.id]:
                return
            else:
                del self.ignore_list[message.author.id]

        if config.get("always_online", False):
            if message.author.id == self.partner_id:
                await self.respond_to_partner(message)
            else:
                await self.handle_stranger(message)
        else:
            if self.is_in_session(server_id):
                if message.author.id == self.partner_id:
                    await self.respond_to_partner(message)
                else:
                    await self.handle_stranger(message)

    async def send_with_delay(self, channel, content):
        server_id = str(channel.guild.id)
        config = self.server_configs[server_id]

        if config.get("always_online", False):
            await channel.send(content)
            return
        slowmode = config.get("slowmode_override")
        if slowmode is None:
            slowmode = channel.slowmode_delay or 0
        delay = random.randint(slowmode + 1, slowmode + 30)
        await asyncio.sleep(delay)
        await channel.send(content)

    def is_in_session(self, server_id):
        now = datetime.utcnow()
        if server_id in self.current_sessions:
            if now < self.current_sessions[server_id]:
                return True
        if random.random() < 0.02:
            duration = random.randint(45, 120)
            self.current_sessions[server_id] = now + timedelta(minutes=duration)
            return True
        return False