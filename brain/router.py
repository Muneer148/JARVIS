from __future__ import annotations

from brain import nvidia, ollama, omniroute, openrouter
from config.settings import (
    BRAIN_MODE,
    MODEL,
    NVIDIA_MODEL,
    OPENROUTER_MODEL,
    OMNIROUTE_MODEL,
)


CLOUD_PROVIDERS = ("omniroute", "nvidia", "openrouter")


def choose_provider(user_text: str) -> str:
    """Choose the model gateway while keeping JARVIS local-first.

    Modes:
      local       -> Ollama only
      cloud       -> first configured cloud gateway, then local fallback
      nvidia      -> NVIDIA only, with local fallback on failure
      openrouter  -> OpenRouter only, with local fallback on failure
      omniroute   -> local OmniRoute gateway only, with local fallback
      auto        -> local for routine work; configured cloud escalation for
                     explicitly complex/long requests.
    """
    if BRAIN_MODE in {"local", "nvidia", "openrouter", "omniroute", "cloud"}:
        return BRAIN_MODE

    text = user_text.lower()
    cloud_markers = (
        "deep analysis", "complex", "difficult", "architecture", "debug this",
        "analyze this code", "large codebase", "reason deeply", "long context",
        "use the cloud", "frontier model", "maximum intelligence",
    )

    if len(user_text) <= 1200 and not any(marker in text for marker in cloud_markers):
        return "local"

    for provider in CLOUD_PROVIDERS:
        if provider == "omniroute" and omniroute.available():
            return provider
        if provider == "nvidia" and nvidia.available():
            return provider
        if provider == "openrouter" and openrouter.available():
            return provider
    return "local"


def _cloud_chat(messages: list[dict[str, str]]) -> tuple[str, str]:
    if omniroute.available():
        try:
            return omniroute.chat(messages, OMNIROUTE_MODEL), "omniroute"
        except RuntimeError:
            pass
    if nvidia.available():
        try:
            return nvidia.chat(messages, NVIDIA_MODEL), "nvidia"
        except RuntimeError:
            pass
    if openrouter.available():
        try:
            return openrouter.chat(messages, OPENROUTER_MODEL), "openrouter"
        except RuntimeError:
            pass
    return ollama.chat(messages, MODEL), "local-fallback"


def chat(messages: list[dict[str, str]], user_text: str) -> tuple[str, str]:
    provider = choose_provider(user_text)

    if provider == "cloud":
        return _cloud_chat(messages)

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
