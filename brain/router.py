from __future__ import annotations

from brain import nvidia, ollama, omniroute, openrouter
from config.settings import (
    BRAIN_MODE,
    MODEL,
    NVIDIA_MODEL,
    OPENROUTER_MODEL,
    OMNIROUTE_MODEL,
)


def choose_provider(user_text: str) -> str:
    """Choose the model gateway while keeping JARVIS local-first.

    Modes:
      local       -> Ollama only
      nvidia      -> NVIDIA only, with local fallback on failure
      openrouter  -> OpenRouter only, with local fallback on failure
      omniroute   -> OmniRoute only, with local fallback on failure
      auto        -> local for routine work; optional cloud escalation for
                     explicitly complex/long requests.
    """
    if BRAIN_MODE in {"local", "nvidia", "openrouter", "omniroute"}:
        return BRAIN_MODE

    text = user_text.lower()
    cloud_markers = (
        "deep analysis", "complex", "difficult", "architecture", "debug this",
        "analyze this code", "large codebase", "reason deeply", "long context",
    )

    if len(user_text) <= 1200 and not any(marker in text for marker in cloud_markers):
        return "local"

    # Prefer the user's own OmniRoute gateway when configured. It can route
    # across many upstream providers without JARVIS needing provider-specific
    # logic. Direct NVIDIA/OpenRouter remain available as explicit fallbacks.
    if omniroute.available():
        return "omniroute"
    if nvidia.available():
        return "nvidia"
    if openrouter.available():
        return "openrouter"
    return "local"


def chat(messages: list[dict[str, str]], user_text: str) -> tuple[str, str]:
    provider = choose_provider(user_text)

    if provider == "omniroute":
        try:
            return omniroute.chat(messages, OMNIROUTE_MODEL), "omniroute"
        except RuntimeError:
            pass

    if provider == "nvidia":
        try:
            return nvidia.chat(messages, NVIDIA_MODEL), "nvidia"
        except RuntimeError:
            pass

    if provider == "openrouter":
        try:
            return openrouter.chat(messages, OPENROUTER_MODEL), "openrouter"
        except RuntimeError:
            pass

    return ollama.chat(messages, MODEL), "local-fallback" if provider != "local" else "local"
