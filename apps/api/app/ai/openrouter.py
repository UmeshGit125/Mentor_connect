"""Minimal OpenRouter client with the small slice of the Anthropic SDK shape that live.py uses.

`client.messages.create(...)` returns an object with `.stop_reason` and `.content[*].type/.text`,
so live.py and its test double do not care which provider sits behind it.
"""

from types import SimpleNamespace
from typing import Any

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class _Messages:
    def __init__(self, api_key: str, timeout: float) -> None:
        self._api_key = api_key
        self._timeout = timeout

    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        system: str,
        messages: list[dict[str, str]],
        output_config: dict[str, Any],
    ) -> Any:
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "answer",
                    "strict": True,
                    "schema": output_config["format"]["schema"],
                },
            },
        }
        response = httpx.post(
            OPENROUTER_URL,
            json=body,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        choice = response.json()["choices"][0]
        finish = choice.get("finish_reason")
        stop_reason = {"length": "max_tokens", "content_filter": "refusal"}.get(finish, "end_turn")
        text = choice["message"].get("content") or ""
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)] if text else [],
            stop_reason=stop_reason,
        )


class OpenRouter:
    def __init__(self, api_key: str, timeout: float) -> None:
        self.messages = _Messages(api_key, timeout)
