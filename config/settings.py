from __future__ import annotations

import os
from pathlib import Path

OLLAMA_URL = os.getenv("JARVIS_OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("JARVIS_MODEL", "qwen3:8b")
DOWNLOADS_DIR = Path(os.getenv("JARVIS_DOWNLOADS_DIR", str(Path.home() / "Downloads"))).expanduser().resolve()
TERMINAL_ENABLED = os.getenv("JARVIS_TERMINAL_ENABLED", "false").lower() == "true"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("JARVIS_REQUEST_TIMEOUT", "180"))
MAX_TOOL_ROUNDS = int(os.getenv("JARVIS_MAX_TOOL_ROUNDS", "5"))
