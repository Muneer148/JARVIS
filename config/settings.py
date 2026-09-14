from __future__ import annotations

import os
from pathlib import Path

OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("JARVIS_MODEL", "qwen3:8b")
DOWNLOADS_DIR = Path(os.getenv("JARVIS_DOWNLOADS_DIR", str(Path.home() / "Downloads"))).expanduser().resolve()
TERMINAL_ENABLED = os.getenv("JARVIS_TERMINAL_ENABLED", "false").lower() == "true"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("JARVIS_REQUEST_TIMEOUT", "180"))
MAX_TOOL_ROUNDS = int(os.getenv("JARVIS_MAX_TOOL_ROUNDS", "5"))

# Model routing. auto = local first; optional gateways are used only when
# configured and the request is selected for escalation.
BRAIN_MODE = os.getenv("JARVIS_BRAIN_MODE", "auto").lower()
NVIDIA_MODEL = os.getenv("JARVIS_NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
OPENROUTER_MODEL = os.getenv("JARVIS_OPENROUTER_MODEL", "openai/gpt-5")
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").rstrip("/")
OMNIROUTE_MODEL = os.getenv("JARVIS_OMNIROUTE_MODEL", "auto")
