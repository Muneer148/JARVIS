from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from config.settings import REQUEST_TIMEOUT_SECONDS

NVIDIA_URL = os.getenv("JARVIS_NVIDIA_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("JARVIS_NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")


def available() -> bool:
    return bool(NVIDIA_API_KEY.strip())


def chat(messages: list[dict[str, str]], model: str | None = None) -> str:
    if not available():
        raise RuntimeError("NVIDIA_API_KEY is not configured. Add it to your local environment; never commit the key to Git.")

    payload: dict[str, Any] = {
        "model": model or NVIDIA_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 4096,
        "stream": False,
    }
    request = urllib.request.Request(
        NVIDIA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NVIDIA API error {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach NVIDIA API: {exc.reason}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Unexpected NVIDIA response: {data!r}")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"NVIDIA response did not contain text content: {data!r}")
    return content.strip()
