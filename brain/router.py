from __future__ import annotations

from brain import nvidia, ollama
from config.settings import BRAIN_MODE, MODEL, NVIDIA_MODEL


def choose_provider(user_text: str) -> str:
    if BRAIN_MODE in {"local", "nvidia"}:
        return BRAIN_MODE
    # Auto mode keeps routine/private operations local. Longer or explicitly
    # difficult reasoning can use the optional NVIDIA hosted endpoint.
    text = user_text.lower()
    cloud_markers = (
        "deep analysis", "complex", "difficult", "architecture", "debug this",
        "analyze this code", "large codebase", "reason deeply", "long context",
    )
    if nvidia.available() and (len(user_text) > 1200 or any(marker in text for marker in cloud_markers)):
        return "nvidia"
    return "local"


def chat(messages: list[dict[str, str]], user_text: str) -> tuple[str, str]:
    provider = choose_provider(user_text)
    if provider == "nvidia":
        try:
            return nvidia.chat(messages, NVIDIA_MODEL), "nvidia"
        except RuntimeError:
            # Local-first means a temporary cloud failure never destroys the
            # core assistant. The caller still receives a valid model result.
            return ollama.chat(messages, MODEL), "local-fallback"
    return ollama.chat(messages, MODEL), "local"
