from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from config.settings import OLLAMA_URL, REQUEST_TIMEOUT_SECONDS


def chat(messages: list[dict[str, str]], model: str) -> str:
    payload = {"model": model, "messages": messages, "stream": False}
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data: dict[str, Any] = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not reach Ollama. Make sure Ollama is running and the model is installed."
        ) from exc
    message = data.get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"Unexpected Ollama response: {data!r}")
    return content.strip()
