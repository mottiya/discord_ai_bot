from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_xai import ChatXAI

if TYPE_CHECKING:
    from src.settings import Settings


async def get_model(settings: "Settings") -> BaseChatModel:
    """
    Создает и возвращает модель чата на основе настроек.

    Поддерживает разные провайдеры через интерфейс BaseChatModel.
    Поддерживает OpenAI, xAI (Grok) и Groq.

    Args:
        settings: Настройки приложения с параметрами AI

    Returns:
        Экземпляр модели чата, реализующий BaseChatModel
    """
    model_name_lower = settings.ai.model.lower()

    if model_name_lower.startswith("grok"):
        return ChatXAI(
            model=settings.ai.model,
            temperature=settings.ai.temperature,
            max_tokens=settings.ai.max_tokens,
            top_p=settings.ai.top_p,
            api_key=settings.ai.api_key,
        )
    elif model_name_lower.startswith("gpt") or model_name_lower.startswith("o1"):
        return ChatOpenAI(
            model=settings.ai.model,
            temperature=settings.ai.temperature,
            max_tokens=settings.ai.max_tokens,
            top_p=settings.ai.top_p,
            api_key=settings.ai.api_key,
        )
    elif (
        model_name_lower.startswith("mixtral")
        or model_name_lower.startswith("llama")
        or model_name_lower.startswith("gemma")
        or model_name_lower.startswith("qwen")
    ):
        return ChatGroq(
            model=settings.ai.model,
            temperature=settings.ai.temperature,
            max_tokens=settings.ai.max_tokens,
            api_key=settings.ai.api_key,
        )
    else:
        # По умолчанию используем OpenAI
        return ChatOpenAI(
            model=settings.ai.model,
            temperature=settings.ai.temperature,
            max_tokens=settings.ai.max_tokens,
            top_p=settings.ai.top_p,
            api_key=settings.ai.api_key,
        )
