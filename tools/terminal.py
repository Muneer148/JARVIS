from __future__ import annotations

import subprocess
from typing import Any

from config.settings import TERMINAL_ENABLED


def terminal(command: str) -> dict[str, Any]:
    if not TERMINAL_ENABLED:
        return {"status": "blocked", "reason": "Terminal tool is disabled. Set JARVIS_TERMINAL_ENABLED=true only after reviewing the security model."}
    if not command.strip():
        return {"status": "error", "reason": "Empty command"}
    dangerous = ["format ", "diskpart", "shutdown", "rmdir /s", "del /s", "Remove-Item -Recurse", "rm -rf"]
    lowered = command.lower()
    if any(token.lower() in lowered for token in dangerous):
        return {"status": "blocked", "reason": "Potentially destructive command blocked by safety policy."}
    try:
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return {
            "status": "ok" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "reason": "Command timed out after 60 seconds."}
