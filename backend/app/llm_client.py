from __future__ import annotations

from typing import Any

import httpx
import time

from .config import settings
from .openai_client import chat_completion as openai_chat_completion, get_client as openai_get_client


def _provider() -> str:
    return (settings.llm_provider or 'gemini').strip().lower()


def _gemini_payload(messages: list[dict[str, Any]]) -> dict[str, Any]:
    system_parts: list[str] = []
    contents: list[dict[str, Any]] = []

    for message in messages:
        role = message.get('role')
        content = message.get('content', '')
        if role == 'system':
            if content:
                system_parts.append(content)
            continue
        gem_role = 'model' if role == 'assistant' else 'user'
        contents.append({
            'role': gem_role,
            'parts': [{'text': content}]
        })

    payload: dict[str, Any] = {
        'contents': contents,
        'generationConfig': {
            'temperature': settings.llm_temperature,
        },
    }

    if system_parts:
        payload['system_instruction'] = {
            'parts': [{'text': "

".join(system_parts)}]
        }

    return payload


def gemini_chat_completion(messages: list[dict[str, Any]]) -> str:
    api_key = (settings.gemini_api_key or '').strip()
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY is not set')

    base_url = (settings.gemini_base_url or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')
    url = f"{base_url}/models/{settings.gemini_model}:generateContent"

    payload = _gemini_payload(messages)
    headers = {
        'x-goog-api-key': api_key,
    }

    retries = 3
    delay = 1.0
    last_exc: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=settings.llm_timeout_seconds)
            response.raise_for_status()
            data = response.json()
            try:
                return data['candidates'][0]['content']['parts'][0]['text']
            except Exception as exc:
                raise RuntimeError(f"Unexpected Gemini response: {data}") from exc
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code if exc.response else None
            if status in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError('Gemini request failed')


def chat_completion(messages: list[dict[str, Any]]) -> str:
    provider = _provider()
    if provider in {'openai', 'openai_compatible'}:
        return openai_chat_completion(messages)
    if provider == 'gemini':
        return gemini_chat_completion(messages)
    raise RuntimeError(f"Unsupported LLM provider: {provider}")


def health_check() -> dict[str, Any]:
    provider = _provider()

    if provider in {'openai', 'openai_compatible'}:
        client = openai_get_client()
        if hasattr(client, 'models'):
            _ = client.models.list()
        else:
            client.chat.completions.create(
                model=settings.openai_model,
                messages=[{'role': 'user', 'content': 'ping'}],
                max_tokens=1,
                temperature=0,
            )
        return {
            'status': 'ok',
            'provider': provider,
            'model': settings.openai_model,
            'base_url': settings.openai_base_url,
        }

    if provider == 'gemini':
        api_key = (settings.gemini_api_key or '').strip()
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY is not set')
        base_url = (settings.gemini_base_url or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')
        url = f"{base_url}/models"
        response = httpx.get(url, headers={'x-goog-api-key': api_key}, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        return {
            'status': 'ok',
            'provider': provider,
            'model': settings.gemini_model,
            'base_url': base_url,
        }

    raise RuntimeError(f"Unsupported LLM provider: {provider}")
