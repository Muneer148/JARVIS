from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from config.settings import REQUEST_TIMEOUT_SECONDS

OPENROUTER_URL = os.getenv("JARVIS_OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def available() -> bool:
    return bool(OPENROUTER_API_KEY.strip())


def chat(messages: list[dict[str, str]], model: str) -> str:
    if not available():
        raise RuntimeError("OPENROUTER_API_KEY is not configured. Add it to your local environment; never commit the key to Git.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "stream": False,
    }
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/Muneer148/JARVIS",
            "X-Title": "JARVIS",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter API error {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach OpenRouter: {exc.reason}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Unexpected OpenRouter response: {data!r}")
    content = (choices[0].get("message") or {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"OpenRouter response did not contain text content: {data!r}")
    return content.strip()
