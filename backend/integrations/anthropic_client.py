from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from backend.config import settings

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def chat(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.4,
) -> str:
    client = _get_client()
    response = client.messages.create(
        model=model or settings.claude_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def chat_json(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
) -> Any:
    instruction = (
        "\n\nResponda APENAS com um JSON valido, sem texto antes ou depois, "
        "sem blocos de codigo markdown."
    )
    raw = chat(
        system + instruction,
        user,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)
