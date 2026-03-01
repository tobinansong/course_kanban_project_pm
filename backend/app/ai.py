from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("pm.ai")

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"
DEFAULT_APP_NAME = "pm-kanban"


class OpenRouterConfigError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


class OpenRouterResponseError(RuntimeError):
    pass


def run_prompt(prompt: str) -> tuple[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterConfigError("OPENROUTER_API_KEY is not set")

    base_url = os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
    model = DEFAULT_MODEL
    app_name = os.getenv("OPENROUTER_APP_NAME", DEFAULT_APP_NAME)
    referer = os.getenv("OPENROUTER_HTTP_REFERER")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": app_name,
    }
    if referer:
        headers["HTTP-Referer"] = referer

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    start_time = time.perf_counter()
    try:
        response = _post_openrouter(base_url, payload, headers)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OpenRouterRequestError("OpenRouter request failed") from exc
    finally:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info("OpenRouter response in %sms model=%s", duration_ms, model)

    data = response.json()
    content = _extract_content(data)
    return content, model


def _post_openrouter(
    base_url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    url = f"{base_url.rstrip('/')}/chat/completions"
    with httpx.Client(timeout=30.0) as client:
        return client.post(url, json=payload, headers=headers)


def _extract_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterResponseError("OpenRouter response missing content") from exc

    if not isinstance(content, str) or not content.strip():
        raise OpenRouterResponseError("OpenRouter response missing content")

    return content.strip()
