from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from config.settings import REQUEST_TIMEOUT_SECONDS

OMNIROUTE_URL = os.getenv("JARVIS_OMNIROUTE_URL", "http://localhost:20128/v1/chat/completions")
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")


def available() -> bool:
    # OmniRoute is normally local. An API key is optional unless the local
    # gateway has REQUIRE_API_KEY enabled.
    return bool(os.getenv("JARVIS_OMNIROUTE_ENABLED", "false").lower() == "true")


def chat(messages: list[dict[str, str]], model: str) -> str:
    if not available():
        raise RuntimeError("OmniRoute is not enabled. Set JARVIS_OMNIROUTE_ENABLED=true when the local gateway is running.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if OMNIROUTE_API_KEY.strip():
        headers["Authorization"] = f"Bearer {OMNIROUTE_API_KEY}"

    request = urllib.request.Request(
        OMNIROUTE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OmniRoute API error {exc.code}: {body[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach OmniRoute: {exc.reason}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Unexpected OmniRoute response: {data!r}")
    content = (choices[0].get("message") or {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"OmniRoute response did not contain text content: {data!r}")
    return content.strip()
