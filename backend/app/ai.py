from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx
from pydantic import ValidationError

from .schemas import AiChatMessage, AiStructuredOutput

logger = logging.getLogger("pm.ai")

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"
DEFAULT_APP_NAME = "pm-kanban"

STRUCTURED_SYSTEM_PROMPT = (
    "You are an assistant for a kanban board."
    " Respond ONLY with valid JSON that matches this schema:"
    " {\"message\": string, \"operations\": array}."
    " operations is optional but must be an array when present."
    " Each operation is one of:"
    " {\"type\": \"rename_column\", \"columnId\": string, \"title\": string},"
    " {\"type\": \"create_card\", \"columnId\": string, \"title\": string, \"details\": string|null},"
    " {\"type\": \"update_card\", \"cardId\": string, \"title\": string|null, \"details\": string|null},"
    " {\"type\": \"move_card\", \"cardId\": string, \"toColumnId\": string, \"position\": number},"
    " {\"type\": \"delete_card\", \"cardId\": string}."
    " Use only the ids provided in the board state."
    " Do not include markdown or extra keys."
)


class OpenRouterConfigError(RuntimeError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


class OpenRouterResponseError(RuntimeError):
    pass


def run_prompt(prompt: str) -> tuple[str, str]:
    return run_messages([{"role": "user", "content": prompt}])


def run_structured_prompt(
    message: str,
    history: list[AiChatMessage],
    board: dict[str, Any],
) -> tuple[AiStructuredOutput, str]:
    messages = _build_structured_messages(message, history, board)
    content, model = run_messages(messages)
    structured = parse_structured_response(content)
    return structured, model


def run_messages(messages: list[dict[str, str]]) -> tuple[str, str]:
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

    payload: dict[str, Any] = {"model": model, "messages": messages}

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


def parse_structured_response(content: str) -> AiStructuredOutput:
    payload = _strip_json_fence(content)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning("OpenRouter structured response invalid JSON: %s", exc)
        raise OpenRouterResponseError("OpenRouter response was not valid JSON") from exc

    try:
        return AiStructuredOutput.model_validate(data)
    except ValidationError as exc:
        logger.warning(
            "OpenRouter structured response failed schema validation: %s",
            exc,
        )
        raise OpenRouterResponseError(
            "OpenRouter response failed schema validation"
        ) from exc


def _build_structured_messages(
    message: str,
    history: list[AiChatMessage],
    board: dict[str, Any],
) -> list[dict[str, str]]:
    board_json = json.dumps(board, ensure_ascii=True, separators=(",", ":"))
    messages: list[dict[str, str]] = [
        {"role": "system", "content": STRUCTURED_SYSTEM_PROMPT},
        {"role": "system", "content": f"Board state JSON: {board_json}"},
    ]
    messages.extend(
        {"role": item.role, "content": item.content} for item in history
    )
    messages.append({"role": "user", "content": message})
    return messages


def _strip_json_fence(content: str) -> str:
    trimmed = content.strip()
    if not trimmed.startswith("```"):
        return trimmed

    lines = trimmed.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
