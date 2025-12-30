import asyncio
import logging
from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.message_generator import BaseMessageGenerator
from src.resources_manager import SystemContextModel

if TYPE_CHECKING:
    from src.settings import Settings

logger = logging.getLogger(__name__)

# Константы
MAX_MESSAGES_PER_IDENTITY = 30
MAX_TOKENS_LIMIT = 50000
REQUEST_TIMEOUT = 30  # секунды
RETRY_DELAYS = [60, 300, 300]  # секунды: первая через минуту, остальные через 5 минут


class AIMessageGenerator(BaseMessageGenerator):
    def __init__(
        self,
        model: BaseChatModel,
        system_context: SystemContextModel,
        settings: "Settings",
        identity_1_id: int,
        identity_2_id: int,
    ):
        self.model = model
        self.system_context = system_context
        self.settings = settings
        self.identity_1_id = identity_1_id
        self.identity_2_id = identity_2_id

        # История сообщений: список кортежей (identity_id, message_text)
        self.message_history: list[tuple[int, str]] = []

        # Счетчики сообщений для каждой личности
        self.identity_1_message_count = 0
        self.identity_2_message_count = 0

    def _get_identity_context(self, identity_id: int) -> tuple[str, str, str]:
        """Возвращает контекст личности по её ID."""
        if identity_id == self.identity_1_id:
            ctx = self.system_context.identity_1
            return ctx.name, ctx.personality, ctx.background
        elif identity_id == self.identity_2_id:
            ctx = self.system_context.identity_2
            return ctx.name, ctx.personality, ctx.background
        else:
            raise ValueError(f"Unknown identity ID: {identity_id}")

    def _build_system_prompt(self, current_identity_id: int) -> str:
        """Строит системный промпт для текущей личности."""
        name, personality, background = self._get_identity_context(current_identity_id)

        # Определяем оппонента
        opponent_id = self.identity_2_id if current_identity_id == self.identity_1_id else self.identity_1_id
        opponent_name, _, _ = self._get_identity_context(opponent_id)

        system_prompt = f"""Ты {name}.

Твоя личность: {personality}
Твой фон: {background}

Ты общаешься с {opponent_name} в Discord. Отвечай естественно, в соответствии со своей личностью.
Будь дружелюбным и вовлеченным в беседу. Отвечай на русском языке."""
        return system_prompt

    def _estimate_tokens(self, messages: list) -> int:
        """
        Оценивает количество токенов в сообщениях.
        Упрощенная оценка: примерно 4 символа = 1 токен для русского языка.
        """
        total_chars = sum(len(str(msg.content)) for msg in messages)
        return total_chars // 4

    def _should_summarize(self, messages: list) -> bool:
        """Проверяет, нужно ли делать суммаризацию."""
        estimated_tokens = self._estimate_tokens(messages)
        return estimated_tokens > MAX_TOKENS_LIMIT

    async def _summarize_history(self, messages_to_summarize: list) -> str:
        """
        Суммаризирует часть истории сообщений используя LangChain summarize chain.
        Использует ту же модель, что и для генерации сообщений.
        """
        try:
            # Используем ту же модель для суммаризации, но с более низкой температурой
            # Сохраняем оригинальные параметры
            original_temperature = getattr(self.model, "temperature", None)

            # Временно устанавливаем низкую температуру для суммаризации
            if hasattr(self.model, "temperature"):
                self.model.temperature = 0.3

            # Формируем текст для суммаризации
            history_text = "\n".join(
                f"{'Bot1' if i % 2 == 0 else 'Bot2'}: {msg.content}" for i, msg in enumerate(messages_to_summarize)
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Ты помощник, который создает краткое резюме диалога. "
                        "Сохрани ключевые темы, важные моменты и общий контекст беседы. "
                        "Ответь на русском языке.",
                    ),
                    ("human", f"Создай краткое резюме следующего диалога:\n\n{history_text}"),
                ]
            )

            chain = prompt | self.model
            result = await chain.ainvoke({})

            # Восстанавливаем оригинальную температуру
            if hasattr(self.model, "temperature") and original_temperature is not None:
                self.model.temperature = original_temperature

            return result.content
        except Exception as e:
            # Восстанавливаем оригинальную температуру в случае ошибки
            if hasattr(self.model, "temperature") and original_temperature is not None:
                self.model.temperature = original_temperature
            logger.warning(f"Ошибка при суммаризации истории: {e}. Продолжаем без суммаризации.")
            return "Предыдущая часть диалога была опущена из-за ограничений контекста."

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Проверяет, можно ли повторить запрос при данной ошибке.
        Не повторяем ошибки доступа (401, 403) и ошибки кредитов.
        """
        error_str = str(error).lower()
        error_repr = repr(error).lower()

        # Проверяем на ошибки доступа и кредитов
        if "403" in error_str or "forbidden" in error_str:
            return False
        if "401" in error_str or "unauthorized" in error_str:
            return False
        if "credits" in error_str or "credits" in error_repr:
            return False
        if "permission" in error_str or "permission" in error_repr:
            return False
        if "does not have permission" in error_str:
            return False

        # Проверяем на ошибки, которые можно повторить
        # Rate limit (429) и server errors (5xx) можно повторить
        if "429" in error_str or "rate limit" in error_str:
            return True
        if "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
            return True

        # Таймауты можно повторить
        if isinstance(error, TimeoutError) or "timeout" in error_str:
            return True

        # По умолчанию повторяем (для неизвестных ошибок)
        return True

    async def _generate_with_retry(self, messages: list) -> str:
        """
        Генерирует ответ с повторными попытками при ошибках.
        Не повторяет ошибки доступа (401, 403) и ошибки кредитов.
        """
        last_error = None

        for attempt, delay in enumerate(RETRY_DELAYS, 1):
            try:
                if attempt > 1:
                    logger.info(f"Повторная попытка {attempt} через {delay} секунд...")
                    await asyncio.sleep(delay)

                # Выполняем запрос с таймаутом
                result = await asyncio.wait_for(
                    self.model.ainvoke(messages),
                    timeout=REQUEST_TIMEOUT,
                )
                return result.content

            except TimeoutError as e:
                last_error = e
                if not self._is_retryable_error(e) or attempt >= len(RETRY_DELAYS):
                    break
                logger.warning(f"Таймаут при запросе к AI (попытка {attempt}/{len(RETRY_DELAYS)})")
            except Exception as e:
                last_error = e
                # Проверяем, можно ли повторить эту ошибку
                if not self._is_retryable_error(e):
                    logger.error(
                        f"Критическая ошибка доступа/кредитов (не повторяем): {e}. "
                        "Проверьте настройки API ключа и наличие кредитов."
                    )
                    break
                if attempt >= len(RETRY_DELAYS):
                    break
                logger.warning(f"Ошибка при запросе к AI (попытка {attempt}/{len(RETRY_DELAYS)}): {e}")

        # Все попытки исчерпаны или критическая ошибка
        error_msg = (
            f"Не удалось сгенерировать сообщение после {attempt} попыток. "
            f"Последняя ошибка: {last_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_error

    async def _prepare_messages(self, current_identity_id: int, opponent_message: str | None) -> list:
        """
        Подготавливает список сообщений для отправки в модель.
        Включает системный промпт, историю и текущее сообщение оппонента.
        """
        messages = []

        # Системный промпт
        system_prompt = self._build_system_prompt(current_identity_id)
        messages.append(SystemMessage(content=system_prompt))

        # История сообщений
        history_messages = []
        for identity_id, msg_text in self.message_history:
            if identity_id == self.identity_1_id:
                role = "Bot1"
            else:
                role = "Bot2"
            history_messages.append(HumanMessage(content=f"{role}: {msg_text}"))

        # Проверяем, нужно ли суммаризировать
        all_messages = messages + history_messages
        if self._should_summarize(all_messages) and len(history_messages) > 5:
            # Суммаризируем первые 70% истории, оставляем последние 30%
            split_point = int(len(history_messages) * 0.7)
            messages_to_summarize = history_messages[:split_point]
            remaining_messages = history_messages[split_point:]

            # Суммаризируем историю
            summary_text = await self._summarize_history(messages_to_summarize)
            messages.append(HumanMessage(content=f"[Резюме предыдущего диалога]: {summary_text}"))
            messages.extend(remaining_messages)
        else:
            messages.extend(history_messages)

        # Текущее сообщение оппонента
        if opponent_message:
            opponent_id = self.identity_2_id if current_identity_id == self.identity_1_id else self.identity_1_id
            opponent_name, _, _ = self._get_identity_context(opponent_id)
            messages.append(HumanMessage(content=f"{opponent_name}: {opponent_message}"))

        return messages

    async def get_next_message(
        self,
        current_identity_id: int,
        opponent_message: str | None = None,
        message_count: int = 0,
    ) -> str | None:
        """
        Генерирует следующее сообщение для указанной личности.

        Args:
            current_identity_id: ID личности, которая должна ответить
            opponent_message: Последнее сообщение оппонента
            message_count: Количество сообщений в текущей сессии (не используется напрямую)

        Returns:
            Сгенерированное сообщение или None, если достигнут лимит сообщений
        """
        # Проверяем лимит сообщений для текущей личности
        if current_identity_id == self.identity_1_id:
            if self.identity_1_message_count >= MAX_MESSAGES_PER_IDENTITY:
                logger.info(f"Достигнут лимит сообщений для identity_1 ({MAX_MESSAGES_PER_IDENTITY})")
                return None
        elif current_identity_id == self.identity_2_id:
            if self.identity_2_message_count >= MAX_MESSAGES_PER_IDENTITY:
                logger.info(f"Достигнут лимит сообщений для identity_2 ({MAX_MESSAGES_PER_IDENTITY})")
                return None
        else:
            raise ValueError(f"Unknown identity ID: {current_identity_id}")

        # Добавляем сообщение оппонента в историю, если оно есть
        if opponent_message:
            opponent_id = self.identity_2_id if current_identity_id == self.identity_1_id else self.identity_1_id
            self.message_history.append((opponent_id, opponent_message))

        # Подготавливаем сообщения для модели
        messages = await self._prepare_messages(current_identity_id, opponent_message)

        # Генерируем ответ с ретраями
        generated_message = await self._generate_with_retry(messages)

        # Добавляем сгенерированное сообщение в историю
        self.message_history.append((current_identity_id, generated_message))

        # Увеличиваем счетчик сообщений
        if current_identity_id == self.identity_1_id:
            self.identity_1_message_count += 1
        else:
            self.identity_2_message_count += 1

        return generated_message
