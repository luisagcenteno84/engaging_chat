from __future__ import annotations

from typing import Any

from openai import OpenAI

from .config import settings


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if settings.openai_base_url:
            _client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url, timeout=settings.openai_timeout_seconds, max_retries=2)
        else:
            _client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds, max_retries=2)
    return _client


def chat_completion(messages: list[dict[str, Any]]) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.4,
        timeout=settings.openai_timeout_seconds,
    )
    return response.choices[0].message.content or ''
