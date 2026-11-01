from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from config.settings import REQUEST_TIMEOUT_SECONDS

# Match OmniRoute's own environment names. A full URL override is retained for
# compatibility with older JARVIS configs.
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").rstrip("/")
OMNIROUTE_URL = os.getenv(
    "JARVIS_OMNIROUTE_URL",
    f"{OMNIROUTE_BASE_URL}/chat/completions",
)
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")
OMNIROUTE_ENABLED = os.getenv("JARVIS_OMNIROUTE_ENABLED", "false").lower() == "true"


def available() -> bool:
    """Return whether OmniRoute is configured as a usable JARVIS gateway.

    OmniRoute's local server is currently protected by an API key. Requiring
    the key here prevents auto-routing from selecting a gateway that will
    predictably return HTTP 401 and then falling back after a wasted request.
    """
    return OMNIROUTE_ENABLED and bool(OMNIROUTE_API_KEY.strip())


def chat(messages: list[dict[str, str]], model: str) -> str:
    if not OMNIROUTE_ENABLED:
        raise RuntimeError(
            "OmniRoute is disabled. Set JARVIS_OMNIROUTE_ENABLED=true when the local gateway is running."
        )
    if not OMNIROUTE_API_KEY.strip():
        raise RuntimeError(
            "OMNIROUTE_API_KEY is not configured. Add the local OmniRoute API key to your environment; never commit it to Git."
        )

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OMNIROUTE_API_KEY}",
    }

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
