import os
import base64
import asyncio
from typing import List, Optional

# Попытка импорта — если библиотека не установлена, пропустим
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import httpx
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

async def _openai_call(model: str, messages: List[dict], images: Optional[List[str]] = None):
    if not OPENAI_AVAILABLE:
        raise ImportError("Требуется: pip install openai")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # Формируем контент
    content = [{"type": "text", "text": messages[-1]["content"]}]
    if images:
        for img_b64 in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=500,
        temperature=0.7
    )
    return resp.choices[0].message.content

async def _anthropic_call(model: str, messages: List[dict], images: Optional[List[str]] = None):
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("Требуется: pip install anthropic")
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # Claude требует system prompt и текст в начале
    text = messages[-1]["content"]
    content = [{"type": "text", "text": text}]
    if images:
        for img_b64 in images:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
            })
    resp = await client.messages.create(
        model=model,
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": content}]
    )
    return resp.content[0].text

async def _google_call(model: str, messages: List[dict], images: Optional[List[str]] = None):
    if not GOOGLE_AVAILABLE:
        raise ImportError("Требуется: pip install google-generativeai")
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model_instance = genai.GenerativeModel(model)
    prompt = messages[-1]["content"]
    if images:
        # Gemini принимает изображения как объекты, но проще через их API напрямую
        # Для упрощения — пока только текст (можно расширить позже)
        pass
    resp = await asyncio.to_thread(model_instance.generate_content, prompt)
    return resp.text

async def _ollama_call(model: str, messages: List[dict], images: Optional[List[str]] = None):
    if not OLLAMA_AVAILABLE:
        raise ImportError("Требуется: pip install httpx")
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/chat"
    prompt = messages[-1]["content"]
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        })
        return resp.json()["message"]["content"]

async def generate_response(
    provider: str,
    model: str,
    messages: List[dict],
    images: Optional[List[str]] = None,
    context: str = ""
) -> str:
    """
    Универсальная функция для генерации ответа от AI.
    
    :param provider: "openai", "anthropic", "google", "ollama"
    :param model: название модели
    :param messages: список сообщений (обычно последнее — текущий запрос)
    :param images: список base64-изображений (PNG)
    :param context: техническая документация из HTML
    :return: ответ от модели
    """
    # Добавляем контекст из документации
    full_prompt = f"""Контекст проекта:
{context[:3000]}  # Ограничиваем длину

Вопрос:
{messages[-1]['content']}"""

    # Обновляем последнее сообщение
    messages = [{"role": "user", "content": full_prompt}]

    try:
        if provider == "openai":
            return await _openai_call(model, messages, images)
        elif provider == "anthropic":
            return await _anthropic_call(model, messages, images)
        elif provider == "google":
            return await _google_call(model, messages, images)
        elif provider == "ollama":
            return await _ollama_call(model, messages, images)
        else:
            raise ValueError(f"Неизвестный провайдер: {provider}")
    except Exception as e:
        return f"[Ошибка AI: {str(e)}] — но я всё равно здесь!"