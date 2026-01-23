from typing import TYPE_CHECKING

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_xai import ChatXAI

if TYPE_CHECKING:
    from src.settings import Settings


async def setup_model(settings: "Settings") -> BaseChatModel:
    model_name_lower = settings.main_ai.model.lower()

    if model_name_lower.startswith("grok"):
        return ChatXAI(
            model=settings.main_ai.model,
            temperature=settings.main_ai.temperature,
            max_tokens=settings.main_ai.max_tokens,
            top_p=settings.main_ai.top_p,
            api_key=settings.main_ai.api_key,
        )
    elif model_name_lower.startswith("gpt") or model_name_lower.startswith("o1"):
        return ChatOpenAI(
            model=settings.main_ai.model,
            temperature=settings.main_ai.temperature,
            max_tokens=settings.main_ai.max_tokens,
            top_p=settings.main_ai.top_p,
            api_key=settings.main_ai.api_key,
        )
    elif (
        model_name_lower.startswith("mixtral")
        or model_name_lower.startswith("llama")
        or model_name_lower.startswith("gemma")
        or model_name_lower.startswith("qwen")
    ):
        return ChatGroq(
            model=settings.main_ai.model,
            temperature=settings.main_ai.temperature,
            max_tokens=settings.main_ai.max_tokens,
            api_key=settings.main_ai.api_key,
        )
    else:
        return ChatOpenAI(
            model=settings.main_ai.model,
            temperature=settings.main_ai.temperature,
            max_tokens=settings.main_ai.max_tokens,
            top_p=settings.main_ai.top_p,
            api_key=settings.main_ai.api_key,
        )
